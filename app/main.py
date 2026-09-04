from pathlib import Path
import os
import time
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

from .db import Base, engine, get_db
from .models import (
    User,
    LearnerProfile,
    ContextFactors,
    StudentSkill,
    StudentCertification,
    StudentLink,
    CareerShiftMatrix,
    DreamPathway,
    ReadinessScorecard,
    GapReport,
    LearningPlan,
    SuccessMantra,
    CampusCourse,
    CourseCoupon,
    LmsCourse,
    LmsModule,
    LmsLecture,
    LmsEnrollment,
    LmsCollaborationPost,
    ExistingJob,
    InstitutionalCollaboration,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    VectorDocument,
    CagCacheRegistry,
    FeedbackLoop,
    AiAuditLog,
    HitlReviewQueue,
    PlatformMoat,
    SecurityPolicyLog,
    ReadinessProceeding,
    MentorSession,
    Session as InterviewSession,
    Question,
    Answer,
    MediaAsset,
)
from .schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionSummary,
    CurrentQuestionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    AnswerEvaluation,
    MediaInfo,
    MediaAnalyticsRequest,
    ReadinessDiagnosisRequest,
    ReportResponse,
    ReportItem,
    ContextFactorsRequest,
    StudentSkillRequest,
    StudentSkillResponse,
    StudentCertificationRequest,
    StudentCertificationResponse,
    StudentLinkRequest,
    StudentLinkResponse,
    CareerShiftRequest,
    CareerShiftResponse,
    LmsLectureResponse,
    LmsModuleResponse,
    LmsCourseResponse,
    LmsEnrollRequest,
    LmsProgressResponse,
    LmsPostRequest,
    LmsCollaborationPostResponse,
    JobSearchResponse,
    MentorshipBookRequest,
    MentorshipUpdateRequest,
    MentorshipSessionResponse,
    SecurityPolicyLogResponse,
    FeedbackLoopResponse,
    PlatformMoatResponse,
    ReadinessProceedingResponse,
    HitlQueueItemResponse,
    MentorRosterItemResponse,
    MentorDiagnosticSnapshotResponse,
    InstitutionAnalyticsResponse,
    EmployerMatchResponse,
)
from .services.ai_provider import (
    generate_questions,
    evaluate_answer,
    save_media_file,
    transcribe_media,
    has_openai,
)
from .services.readiness_engine import (
    get_platform_framework,
    diagnose_readiness,
    get_stream_suggested_skills,
    seed_database_content,
    query_rag_context,
    process_feedback_loop_trigger,
    log_readiness_proceeding,
)
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

# Connection manager for per-session websockets
_session_connections: dict[str, set[WebSocket]] = {}
_session_timer_tasks: dict[str, asyncio.Task] = {}


async def _broadcast(session_id: int, message: dict):
    conns = _session_connections.get(str(session_id), set())
    if not conns:
        return
    text = json.dumps(message)
    to_remove = []
    for ws in list(conns):
        try:
            await ws.send_text(text)
        except Exception:
            to_remove.append(ws)
    for ws in to_remove:
        conns.discard(ws)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="AspireOS ReadyFlow AI Platform")

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
UPLOADS_DIR = ROOT_DIR / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


# Pre-seed on startup
@app.on_event("startup")
def on_startup():
    db = next(get_db())
    seed_database_content(db)
    
    # Initialize a default mock learner user if empty
    if db.query(User).count() == 0:
        default_user = User(username="fresha_aspirant", role="Learner")
        db.add(default_user)
        db.commit()


# --- IT Cybersecurity & Rate Limiting Middleware ---
_rate_limits = {}
 

@app.middleware("http")
async def security_policy_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"

    # ============================================================
    # 1. API RATE LIMITING
    # ============================================================
    is_api_request = request.url.path.startswith("/api/")

    if is_api_request:
        curr_time = time.time()

        # Rate-limit per IP + API endpoint + Method.
        rate_key = f"{client_ip}:{request.method}:{request.url.path}"

        last_time = _rate_limits.get(rate_key, 0)

        # Block only extremely rapid repeated requests
        # to the SAME endpoint.
        if curr_time - last_time < 1.0:
            db = next(get_db())

            log = SecurityPolicyLog(
                ip_address=client_ip,
                category="Rate Limit Check",
                action_attempt=(
                    f"Repeated API request to {request.url.path} "
                    f"triggered click rate-limiting threshold."
                ),
                status="Blocked",
            )

            db.add(log)
            db.commit()

            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many repeated API requests. "
                        "Please slow down."
                    )
                },
            )

        _rate_limits[rate_key] = curr_time

    # ============================================================
    # 2. MULTIPART UPLOAD SECURITY
    # ============================================================
    #
    # IMPORTANT:
    # Do NOT call await request.form() here.
    #
    # FastAPI needs to read the multipart body itself in order
    # to populate:
    #
    #     Form(...)
    #     File(...)
    #
    # Calling request.form() in middleware can consume the request
    # body and cause the endpoint to return 422.
    #
    # We therefore perform request-level size validation here.
    # Individual file extension/size validation is handled inside
    # the upload endpoint.
    # ============================================================

    content_type = request.headers.get("content-type", "").lower()

    if (
        request.method == "POST"
        and "multipart/form-data" in content_type
    ):
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                request_size_mb = int(content_length) / (1024 * 1024)

                # Maximum multipart request size: 10 MB
                if request_size_mb > 10.0:
                    db = next(get_db())

                    log = SecurityPolicyLog(
                        ip_address=client_ip,
                        category="Mime Type Validation",
                        action_attempt=(
                            f"Blocked multipart upload request "
                            f"because request size was "
                            f"{request_size_mb:.2f}MB."
                        ),
                        status="Blocked",
                    )

                    db.add(log)
                    db.commit()

                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": (
                                "File too large (Max 10MB). "
                                "Upload blocked."
                            )
                        },
                    )

            except (ValueError, TypeError):
                # Ignore invalid/missing Content-Length.
                # Endpoint-level validation will handle the file.
                pass

    # ============================================================
    # 3. PROCESS REQUEST
    # ============================================================
    response = await call_next(request)

    # ============================================================
    # 4. SECURITY HEADERS
    # ============================================================

    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
        "https://fonts.googleapis.com "
        "https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "media-src 'self' blob: data:;"
    )

    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["X-Frame-Options"] = "DENY"

    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    return response


# --- Mock Authentication switcher ---

CURRENT_USER_ID = 1


@app.get("/api/auth/current")
def get_current_user(db: Session = Depends(get_db)):
    u = db.get(User, CURRENT_USER_ID)
    if not u:
        u = db.query(User).first()
    return {"user_id": u.id, "username": u.username, "role": u.role}


@app.post("/api/auth/role")
def switch_role(role: str, db: Session = Depends(get_db)):
    u = db.get(User, CURRENT_USER_ID)
    if not u:
        u = db.query(User).first()
    u.role = role
    db.commit()
    return {"username": u.username, "role": u.role}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/framework")
def framework_details(db: Session = Depends(get_db)):
    base_framework = get_platform_framework()
    # Fetch learner's proceedings
    proceedings = db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID).all()
    completed_stages = {p.flow_stage: p.created_at for p in proceedings}
    
    for flow in base_framework["universal_flow"]:
        if flow["stage"] in completed_stages:
            flow["completed"] = True
            flow["completed_at"] = completed_stages[flow["stage"]].isoformat() if completed_stages[flow["stage"]] else None
        else:
            flow["completed"] = False
            flow["completed_at"] = None
    return base_framework


@app.post("/api/readiness/diagnose")
def diagnose_readiness_profile(payload: ReadinessDiagnosisRequest, db: Session = Depends(get_db)):
    # count user credentials for boosts
    skills_count = db.query(StudentSkill).filter(StudentSkill.learner_id == CURRENT_USER_ID).count()
    certifications_count = db.query(StudentCertification).filter(StudentCertification.learner_id == CURRENT_USER_ID, StudentCertification.verification_status == "Verified").count()
    
    links = db.query(StudentLink).filter(StudentLink.learner_id == CURRENT_USER_ID).first()
    links_count = 0
    if links:
        if links.github_url: links_count += 1
        if links.linkedin_url: links_count += 1
        
    data = payload.model_dump()
    data["skills_count"] = skills_count
    data["certifications_count"] = certifications_count
    data["links_count"] = links_count

    diag = diagnose_readiness(data)
    
    # Save/update diagnostic values in db
    scorecard = diag["scorecard"]
    existing_sc = db.query(ReadinessScorecard).filter(ReadinessScorecard.learner_id == CURRENT_USER_ID, ReadinessScorecard.assessment_type == "Baseline").first()
    
    sc_type = "Baseline"
    if existing_sc:
        sc_type = "Current"
        
    db_scorecard = ReadinessScorecard(
        learner_id=CURRENT_USER_ID,
        purpose_clarity=scorecard["dimensions"][0]["score"],
        self_awareness_confidence=scorecard["dimensions"][1]["score"],
        communication_readiness=scorecard["dimensions"][2]["score"],
        digital_ai_readiness=scorecard["dimensions"][3]["score"],
        domain_readiness=scorecard["dimensions"][4]["score"],
        problem_solving=scorecard["dimensions"][5]["score"],
        collaboration_leadership=scorecard["dimensions"][6]["score"],
        career_readiness=scorecard["dimensions"][7]["score"],
        portfolio_evidence=scorecard["dimensions"][8]["score"],
        total_score=scorecard["total_score"],
        readiness_level=scorecard["level"],
        CARI=scorecard["CARI"],
        CCQ=scorecard["CCQ"],
        resilience_index=scorecard["resilience_index"],
        assessment_type=sc_type,
        pcs=diag["institution_analytics"]["portfolio_completion_percent"],
        success_mantras_progress=0
    )
    db.add(db_scorecard)
    
    # Ingest learning plan into DB if not exists
    existing_plan = db.query(LearningPlan).filter(LearningPlan.learner_id == CURRENT_USER_ID).first()
    if not existing_plan:
        plan_dict = []
        for task in diag["development_plan"]["day_30"]:
            plan_dict.append({"task": task, "completed": False})
        for task in diag["development_plan"]["day_60"]:
            plan_dict.append({"task": task, "completed": False})
        for task in diag["development_plan"]["day_90"]:
            plan_dict.append({"task": task, "completed": False})

        db_plan = LearningPlan(
            learner_id=CURRENT_USER_ID,
            plan_type="30-60-90 Day Plan",
            weekly_tasks_json=json.dumps(plan_dict),
            status="Active"
        )
        db.add(db_plan)
        db.commit()

        if db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID, ReadinessProceeding.flow_stage == "Design").count() == 0:
            log_readiness_proceeding(db, CURRENT_USER_ID, "Design", "Generated active Learning Plan from diagnostics.", {}, "Follow the weekly plan items to improve readiness.")

    db.commit()

    # Log to proceedings audit ledger
    log_readiness_proceeding(
        db,
        CURRENT_USER_ID,
        "Diagnose",
        "Completed comprehensive diagnostic assessment.",
        {"total_score": scorecard["total_score"], "CARI": scorecard["CARI"], "CCQ": scorecard["CCQ"], "resilience_index": scorecard["resilience_index"]},
        diag["next_best_action"]
    )
    
    # Update Learner Profile
    prof = db.query(LearnerProfile).filter(LearnerProfile.user_id == CURRENT_USER_ID).first()
    if not prof:
        prof = LearnerProfile(user_id=CURRENT_USER_ID)
        db.add(prof)
    
    dp = diag.get("dream_profile", {})
    if dp:
        prof.dream_statement = dp.get("dream_statement", prof.dream_statement)
        prof.purpose_statement = dp.get("purpose_statement", prof.purpose_statement)
        prof.target_roles = dp.get("target_role", prof.target_roles)
        prof.stream = dp.get("stream", prof.stream)
    db.commit()
    
    # Insert Gap Reports
    gaps = diag.get("gaps", [])
    # First, clear old gaps for baseline
    db.query(GapReport).filter(GapReport.learner_id == CURRENT_USER_ID).delete()
    for g in gaps:
        db.add(GapReport(
            learner_id=CURRENT_USER_ID,
            gap_type=g.get("gap_type", "Unknown gap"),
            symptoms=g.get("symptoms", ""),
            root_cause=g.get("root_cause", ""),
            severity=g.get("severity", "medium"),
            recommended_fix=g.get("recommended_fix", ""),
            evidence_required=g.get("evidence_required", "Not specified")
        ))
    db.commit()

    # Process feedback loops check
    process_feedback_loop_trigger(db, CURRENT_USER_ID, f"Diagnose: Scorecard evaluated.", scorecard["total_score"])

    return diag


# --- ONBOARDING PROFILE & CONTEXT FACTORS ENDPOINTS ---
@app.get("/api/learner/profile")
def get_profile(db: Session = Depends(get_db)):
    prof = db.query(LearnerProfile).filter(LearnerProfile.user_id == CURRENT_USER_ID).first()
    if not prof:
        prof = LearnerProfile(user_id=CURRENT_USER_ID)
        db.add(prof)
        db.commit()
        db.refresh(prof)
    return prof


@app.post("/api/learner/profile")
def update_profile(stream: str = Form(...), experience_level: str = Form(...), location: str = Form(...), dream_statement: str = Form(...), purpose_statement: str = Form(...), strengths: str = Form(...), fears: str = Form(...), target_roles: str = Form(...), db: Session = Depends(get_db)):
    prof = db.query(LearnerProfile).filter(LearnerProfile.user_id == CURRENT_USER_ID).first()
    if not prof:
        prof = LearnerProfile(user_id=CURRENT_USER_ID)
        db.add(prof)
    prof.stream = stream
    prof.experience_level = experience_level
    prof.location = location
    prof.dream_statement = dream_statement
    prof.purpose_statement = purpose_statement
    prof.strengths = strengths
    prof.fears = fears
    prof.target_roles = target_roles
    db.commit()
    
    # Log stage transition to Proceedings
    log_readiness_proceeding(
        db, 
        CURRENT_USER_ID, 
        "Dream", 
        f"Saved dream statement for {target_roles}.", 
        {"dream": target_roles}, 
        "Execute discover stage to map skill requirements."
    )
    
    return {"message": "Profile updated successfully"}


@app.get("/api/learner/context")
def get_context_factors(db: Session = Depends(get_db)):
    cf = db.query(ContextFactors).filter(ContextFactors.learner_id == CURRENT_USER_ID).first()
    if not cf:
        cf = ContextFactors(learner_id=CURRENT_USER_ID)
        db.add(cf)
        db.commit()
        db.refresh(cf)
    return cf


@app.post("/api/learner/context")
def update_context_factors(payload: ContextFactorsRequest, db: Session = Depends(get_db)):
    cf = db.query(ContextFactors).filter(ContextFactors.learner_id == CURRENT_USER_ID).first()
    if not cf:
        cf = ContextFactors(learner_id=CURRENT_USER_ID)
        db.add(cf)
    cf.family_pressure = payload.family_pressure
    cf.financial_dependency = payload.financial_dependency
    cf.confidence_baseline = payload.confidence_baseline
    cf.stress_baseline = payload.stress_baseline
    cf.resilience_rating = payload.resilience_rating
    cf.income_tier = payload.income_tier
    cf.city_tier = payload.city_tier
    cf.college_tier = payload.college_tier
    db.commit()
    return {"message": "Context factors logged"}


# --- SKILLS & CREDENTIALS REGISTRY ENDPOINTS ---
@app.get("/api/learner/skills", response_model=List[StudentSkillResponse])
def get_learner_skills(db: Session = Depends(get_db)):
    return (
        db.query(StudentSkill)
        .filter(StudentSkill.learner_id == CURRENT_USER_ID)
        .order_by(StudentSkill.id.desc())
        .all()
    )


@app.post("/api/learner/skills", response_model=StudentSkillResponse)
def add_learner_skill(
    payload: StudentSkillRequest,
    db: Session = Depends(get_db)
):
    # Prevent duplicate skills for the same learner
    existing_skill = (
        db.query(StudentSkill)
        .filter(
            StudentSkill.learner_id == CURRENT_USER_ID,
            StudentSkill.name.ilike(payload.name.strip())
        )
        .first()
    )

    if existing_skill:
        return existing_skill

    skill = StudentSkill(
        learner_id=CURRENT_USER_ID,
        name=payload.name.strip(),
        category=payload.category,
        proficiency=payload.proficiency,
        verification_status="Self-Reported"
    )

    db.add(skill)
    db.commit()
    db.refresh(skill)

    return skill


@app.delete("/api/learner/skills/{skill_id}")
def delete_learner_skill(
    skill_id: int,
    db: Session = Depends(get_db)
):
    skill = (
        db.query(StudentSkill)
        .filter(
            StudentSkill.id == skill_id,
            StudentSkill.learner_id == CURRENT_USER_ID
        )
        .first()
    )

    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found."
        )

    db.delete(skill)
    db.commit()

    return {
        "message": "Skill removed successfully."
    }


@app.get("/api/learner/certifications", response_model=List[StudentCertificationResponse])
def get_learner_certifications(db: Session = Depends(get_db)):
    certs = db.query(StudentCertification).filter(StudentCertification.learner_id == CURRENT_USER_ID).all()
    results = []
    for cert in certs:
        cert_dict = {
            "id": cert.id,
            "title": cert.title,
            "issuer": cert.issuer,
            "issue_date": cert.issue_date,
            "credential_id": cert.credential_id,
            "verification_status": cert.verification_status,
            "file_url": cert.file_url,
            "reviewer_notes": "--"
        }
        hitl = db.query(HitlReviewQueue).filter(
            HitlReviewQueue.reference_id == cert.id,
            HitlReviewQueue.task_type == "Certification Review"
        ).order_by(HitlReviewQueue.id.desc()).first()
        
        if hitl and hitl.reviewer_notes:
            cert_dict["reviewer_notes"] = hitl.reviewer_notes
        elif cert.verification_status == "Pending Review":
            cert_dict["reviewer_notes"] = "Pending mentor review"
            
        results.append(cert_dict)
    return results


@app.post("/api/learner/certifications", response_model=StudentCertificationResponse)
def upload_learner_certification(
    title: str = Form(...),
    issuer: str = Form(...),
    issue_date: str = Form(None),
    credential_id: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    file_url = None
    if file:
        uploads_root = Path(UPLOADS_DIR).resolve()
        target_path = uploads_root / f"cert-{uuid4().hex}-{file.filename}"
        with open(target_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        file_url = f"/uploads/{target_path.name}"

    cert = StudentCertification(
        learner_id=CURRENT_USER_ID,
        title=title,
        issuer=issuer,
        issue_date=issue_date,
        credential_id=credential_id,
        verification_status="Pending Review",
        file_url=file_url
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)

    hitl = HitlReviewQueue(
        learner_id=CURRENT_USER_ID,
        reference_id=cert.id,
        task_type="Certification Review",
        flag_reason=cert.title,
        status="Pending"
    )
    db.add(hitl)
    db.commit()

    return cert


@app.get("/api/learner/links", response_model=StudentLinkResponse)
def get_learner_links(db: Session = Depends(get_db)):
    links = db.query(StudentLink).filter(StudentLink.learner_id == CURRENT_USER_ID).first()
    if not links:
        links = StudentLink(learner_id=CURRENT_USER_ID)
        db.add(links)
        db.commit()
        db.refresh(links)
    return links


@app.post("/api/learner/links", response_model=StudentLinkResponse)
def update_learner_links(payload: StudentLinkRequest, db: Session = Depends(get_db)):
    links = db.query(StudentLink).filter(StudentLink.learner_id == CURRENT_USER_ID).first()
    if not links:
        links = StudentLink(learner_id=CURRENT_USER_ID)
        db.add(links)
    links.github_url = payload.github_url
    links.linkedin_url = payload.linkedin_url
    links.portfolio_url = payload.portfolio_url
    links.leetcode_url = payload.leetcode_url
    db.commit()
    db.refresh(links)
    return links


# --- CAREER SHIFT MATRIX ENDPOINT ---
@app.post("/api/readiness/career-shift", response_model=CareerShiftResponse)
def calculate_career_shift(payload: CareerShiftRequest, db: Session = Depends(get_db)):
    # simple transferable skill logic mapping shift pathway
    reason = payload.shift_reason.lower()
    gaps = ["Lack of stream-specific projects", "No industry internships"]
    transferable = ["Logical problem-solving", "Presentations"]
    remediation = ["Complete Asperion LMS BootCamp", "Schedule 1-on-1 speaking session"]

    if "engineering" in payload.target_role.lower() or "tech" in payload.target_role.lower():
        gaps.extend(["Data Structures & Algorithms", "Python Programming"])
        remediation.append("Redeem Coursera CS50 coupon")
    elif "management" in payload.target_role.lower() or "business" in payload.target_role.lower():
        gaps.extend(["Excel Analytics", "Client Pitching"])
        remediation.append("Complete Market Research mini-project")

    # save in career shift matrix
    matrix = CareerShiftMatrix(
        learner_id=CURRENT_USER_ID,
        shift_reason=payload.shift_reason,
        capability_delta_json=json.dumps({"gaps": gaps, "transferable": transferable})
    )
    db.add(matrix)
    db.commit()

    if db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID, ReadinessProceeding.flow_stage == "Discover").count() == 0:
        log_readiness_proceeding(db, CURRENT_USER_ID, "Discover", "Calculated career capability delta for shift.", {"gaps": gaps}, "Review identified gaps and begin learning.")

    return CareerShiftResponse(
        transferable_skills=transferable,
        gaps=gaps,
        remediation_delta=remediation,
        reason=payload.shift_reason
    )


# --- 1-on-1 MENTORSHIP BOOKINGS ENDPOINTS ---
@app.get("/api/mentorship/appointments", response_model=List[MentorshipSessionResponse])
def get_mentorship_appointments(db: Session = Depends(get_db)):
    return db.query(MentorSession).filter(MentorSession.learner_id == CURRENT_USER_ID).all()


@app.post("/api/mentorship/appointments", response_model=MentorshipSessionResponse)
def book_mentorship_appointment(payload: MentorshipBookRequest, db: Session = Depends(get_db)):
    meeting_type = payload.meeting_type or "Google Meet"
    
    if meeting_type == "Google Meet":
        meeting_id = f"DEMO-GM-{uuid4().hex[:5].upper()}"
        meet_url = f"/demo/mentorship/{meeting_id}"
    elif meeting_type == "Microsoft Teams":
        meeting_id = f"DEMO-TEAMS-{uuid4().hex[:5].upper()}"
        meet_url = f"/demo/mentorship/{meeting_id}"
    elif meeting_type == "Zoom":
        meeting_id = f"DEMO-ZOOM-{uuid4().hex[:5].upper()}"
        meet_url = f"/demo/mentorship/{meeting_id}"
    elif meeting_type == "Custom Meeting Link":
        meeting_id = f"DEMO-CUSTOM-{uuid4().hex[:5].upper()}"
        meet_url = payload.custom_url if payload.custom_url else f"/demo/mentorship/{meeting_id}"
    else:
        meeting_id = f"DEMO-GM-{uuid4().hex[:5].upper()}"
        meeting_type = "Google Meet"
        meet_url = f"/demo/mentorship/{meeting_id}"

    session = MentorSession(
        learner_id=CURRENT_USER_ID,
        mentor_name=payload.mentor_name,
        date_str=payload.date_str,
        time_str=payload.time_str,
        meeting_type=meeting_type,
        meeting_id=meeting_id,
        meet_url=meet_url,
        notes="Scheduled via AspireOS dashboard.",
        status="Scheduled"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    if db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID, ReadinessProceeding.flow_stage == "Adopt").count() == 0:
        log_readiness_proceeding(db, CURRENT_USER_ID, "Adopt", f"Booked 1-on-1 mentorship session with {payload.mentor_name}.", {"mentor": payload.mentor_name}, "Prepare your questions for the mentorship session.")

    return session


@app.put("/api/mentorship/appointments/{appointment_id}", response_model=MentorshipSessionResponse)
def update_mentorship_appointment(appointment_id: int, payload: MentorshipUpdateRequest, db: Session = Depends(get_db)):
    session = db.query(MentorSession).filter(MentorSession.id == appointment_id, MentorSession.learner_id == CURRENT_USER_ID).first()
    if not session:
        raise HTTPException(status_code=404, detail="Appointment not found")

    meeting_type = payload.meeting_type or "Google Meet"
    
    if meeting_type == "Google Meet":
        meeting_id = f"DEMO-GM-{uuid4().hex[:5].upper()}"
        meet_url = f"/demo/mentorship/{meeting_id}"
    elif meeting_type == "Microsoft Teams":
        meeting_id = f"DEMO-TEAMS-{uuid4().hex[:5].upper()}"
        meet_url = f"/demo/mentorship/{meeting_id}"
    elif meeting_type == "Zoom":
        meeting_id = f"DEMO-ZOOM-{uuid4().hex[:5].upper()}"
        meet_url = f"/demo/mentorship/{meeting_id}"
    elif meeting_type == "Custom Meeting Link":
        meeting_id = f"DEMO-CUSTOM-{uuid4().hex[:5].upper()}"
        meet_url = payload.custom_url if payload.custom_url else f"/demo/mentorship/{meeting_id}"
    else:
        meeting_id = f"DEMO-GM-{uuid4().hex[:5].upper()}"
        meeting_type = "Google Meet"
        meet_url = f"/demo/mentorship/{meeting_id}"

    session.mentor_name = payload.mentor_name
    session.date_str = payload.date_str
    session.time_str = payload.time_str
    session.meeting_type = meeting_type
    session.meeting_id = meeting_id
    session.meet_url = meet_url

    db.commit()
    db.refresh(session)
    return session


@app.get("/demo/mentorship/{meeting_id}", response_class=HTMLResponse)
def demo_mentorship_meeting(meeting_id: str, db: Session = Depends(get_db)):
    # Lookup by meeting_id first, then fallback to meet_url matching
    session = db.query(MentorSession).filter(MentorSession.meeting_id == meeting_id).first()
    if not session:
        session = db.query(MentorSession).filter(MentorSession.meet_url.contains(meeting_id)).first()

    mentor_name = session.mentor_name if session else "Unknown Mentor"
    date_str = session.date_str if session else "Unknown Date"
    time_str = session.time_str if session else "Unknown Time"
    meeting_type = (session.meeting_type if session and session.meeting_type else "Google Meet")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo Mentor Meeting</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #07111f;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}

            .meeting-card {{
                width: 500px;
                background: #101c2c;
                border: 1px solid #26384f;
                border-radius: 16px;
                padding: 35px;
                text-align: center;
                box-shadow: 0 20px 50px rgba(0,0,0,.4);
            }}

            h1 {{
                margin-bottom: 10px;
            }}

            .badge {{
                display: inline-block;
                padding: 6px 14px;
                border-radius: 20px;
                background: #063f35;
                color: #00e6a8;
                margin: 15px 0;
            }}

            .info {{
                text-align: left;
                background: #0b1726;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }}

            .info p {{
                margin: 10px 0;
            }}

            .button {{
                display: inline-block;
                padding: 12px 25px;
                background: #20c9f3;
                color: #001018;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                border: none;
                cursor: pointer;
            }}
            
            .button-secondary {{
                background: #26384f;
                color: #ffffff;
                margin-left: 10px;
            }}

            .note {{
                color: #9aa8ba;
                font-size: 13px;
                margin-top: 20px;
            }}
        </style>
    </head>

    <body>

        <div class="meeting-card">

            <h1>Mentor Meeting</h1>

            <div class="badge">
                DEMO MEETING
            </div>

            <div class="info">
                <p><strong>Mentor:</strong> {mentor_name}</p>
                <p><strong>Meeting Type:</strong> {meeting_type}</p>
                <p><strong>Date:</strong> {date_str}</p>
                <p><strong>Time:</strong> {time_str}</p>
                <p><strong>Status:</strong> Scheduled</p>
                <p><strong>Meeting ID:</strong> {meeting_id}</p>
            </div>

            <p class="note">
                This is a demo meeting for the AspireOS MVP.<br>
                Real meeting-platform integration will be connected later.
            </p>

            <div style="margin-top: 25px;">
                <button onclick="alert('Demo Meeting Joined!')" class="button">
                    Join Demo Meeting
                </button>
                <a href="/" class="button button-secondary">
                    Leave Meeting
                </a>
            </div>

        </div>

    </body>
    </html>
    """

# --- CAMPUS COURSES & COUPONS ENDPOINTS ---
@app.get("/api/courses/campus")
def get_campus_courses(db: Session = Depends(get_db)):
    courses = db.query(CampusCourse).all()
    results = []
    for c in courses:
        coupon = db.query(CourseCoupon).filter(CourseCoupon.course_id == c.id).first()
        results.append({
            "id": c.id,
            "title": c.title,
            "provider": c.provider,
            "tier": c.tier,
            "origin": c.origin,
            "direct_url": c.direct_url,
            "fee_type": c.fee_type,
            "coupon_code": coupon.code if coupon else None
        })
    return results


@app.post("/api/courses/{course_id}/enroll")
def enroll_campus_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.query(CampusCourse).filter(CampusCourse.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check whether learner is already enrolled
    existing = (
        db.query(LmsEnrollment)
        .filter(
            LmsEnrollment.learner_id == CURRENT_USER_ID,
            LmsEnrollment.course_id == course_id
        )
        .first()
    )

    if existing:
        return {
            "success": True,
            "message": "You are already enrolled in this course.",
            "enrollment_id": existing.id
        }

    enrollment = LmsEnrollment(
        learner_id=CURRENT_USER_ID,
        course_id=course_id,
        progress_percent=0,
        completed_lectures_json="[]"
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return {
        "success": True,
        "message": "Enrollment successful.",
        "enrollment_id": enrollment.id
    }


@app.post("/api/courses/{course_id}/payment")
def process_dummy_payment(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.query(CampusCourse).filter(
        CampusCourse.id == course_id
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Free courses do not require payment
    if course.fee_type == "Free":
        raise HTTPException(
            status_code=400,
            detail="This course is free. Payment is not required."
        )

    # Dummy payment only
    return {
        "success": True,
        "payment_status": "SUCCESS",
        "payment_id": f"DEMO-PAY-{course_id}-{CURRENT_USER_ID}",
        "message": "Demo payment successful."
    }

# --- EXISTING JOBS AGGREGATOR ENDPOINTS ---
@app.get("/api/jobs", response_model=List[JobSearchResponse])
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(ExistingJob).all()

    # Get the current student's skills
    student_skills = (
        db.query(StudentSkill)
        .filter(StudentSkill.learner_id == CURRENT_USER_ID)
        .all()
    )

    # Normalize student skill names
    student_skill_names = {
        skill.name.strip().lower()
        for skill in student_skills
        if skill.name
    }

    results = []

    for j in jobs:

        # Get required skills for this job
        required_skills = [
            skill.strip()
            for skill in j.required_skills.split(",")
            if skill.strip()
        ]

        # Find matched and missing skills
        matched_skill_names = []
        missing_skill_names = []

        for skill in required_skills:
            # Substring match: if the required skill is inside any of the user's skills
            if any(skill.lower() in student_skill for student_skill in student_skill_names):
                matched_skill_names.append(skill)
            else:
                missing_skill_names.append(skill)

        # Calculate Fit Index
        if required_skills:
            match_score = round(
                (len(matched_skill_names) / len(required_skills)) * 100
            )
        else:
            match_score = 0

        results.append(
            JobSearchResponse(
                id=j.id,
                title=j.title,
                organization=j.organization,
                type=j.type,
                required_skills=required_skills,
                matched_skills=matched_skill_names,
                missing_skills=missing_skill_names,
                url=j.url,
                match_score=match_score
            )
        )

    # Highest matching jobs first
    results.sort(
        key=lambda job: job.match_score,
        reverse=True
    )

    return results


@app.post("/api/jobs/{job_id}/apply")
def apply_to_job(job_id: int, db: Session = Depends(get_db)):
    from .models import JobApplication
    job = db.query(ExistingJob).filter(ExistingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    existing_app = db.query(JobApplication).filter(JobApplication.learner_id == CURRENT_USER_ID, JobApplication.job_id == job_id).first()
    if existing_app:
        raise HTTPException(status_code=400, detail="Already applied to this job")
        
    app_record = JobApplication(learner_id=CURRENT_USER_ID, job_id=job_id)
    db.add(app_record)
    db.commit()
    
    if db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID, ReadinessProceeding.flow_stage == "Deploy").count() == 0:
        log_readiness_proceeding(db, CURRENT_USER_ID, "Deploy", f"Applied to job: {job.title}", {"job_id": job_id}, "Prepare for potential recruiter interviews.")
        
    return {"status": "success", "message": "Applied successfully"}


# --- ASPERION INTERNAL LMS ENDPOINTS ---
@app.get("/api/lms/courses", response_model=List[LmsCourseResponse])
def get_lms_courses(db: Session = Depends(get_db)):
    courses = db.query(LmsCourse).all()
    results = []
    for c in courses:
        modules_resp = []
        modules = db.query(LmsModule).filter(LmsModule.course_id == c.id).order_by(LmsModule.order_no.asc()).all()
        for m in modules:
            lectures = db.query(LmsLecture).filter(LmsLecture.module_id == m.id).all()
            lectures_resp = [
                LmsLectureResponse(
                    id=l.id,
                    module_id=l.module_id,
                    title=l.title,
                    content_type=l.content_type,
                    content=l.content,
                    mantras=l.mantras
                )
                for l in lectures
            ]
            modules_resp.append(LmsModuleResponse(
                id=m.id,
                title=m.title,
                order_no=m.order_no,
                lectures=lectures_resp
            ))
        results.append(LmsCourseResponse(
            id=c.id,
            title=c.title,
            description=c.description,
            instructor=c.instructor,
            stream=c.stream,
            duration=c.duration,
            difficulty=c.difficulty,
            modules=modules_resp
        ))
    return results


@app.post("/api/lms/courses/{course_id}/enroll")
def enroll_lms_course(course_id: int, db: Session = Depends(get_db)):
    enr = db.query(LmsEnrollment).filter(LmsEnrollment.learner_id == CURRENT_USER_ID, LmsEnrollment.course_id == course_id).first()
    if not enr:
        enr = LmsEnrollment(learner_id=CURRENT_USER_ID, course_id=course_id, progress_percent=0, completed_lectures_json="[]")
        db.add(enr)
        db.commit()
    return {"message": "Enrolled"}


@app.post("/api/lms/courses/{course_id}/progress")
def update_lms_progress(course_id: int, lecture_id: int, db: Session = Depends(get_db)):
    enr = db.query(LmsEnrollment).filter(LmsEnrollment.learner_id == CURRENT_USER_ID, LmsEnrollment.course_id == course_id).first()
    if not enr:
        raise HTTPException(status_code=400, detail="Not enrolled")
    
    completed = json.loads(enr.completed_lectures_json)
    if lecture_id not in completed:
        completed.append(lecture_id)
        enr.completed_lectures_json = json.dumps(completed)
    
    # Calculate progress % based on total lectures
    # hardcoded 2 lectures count
    enr.progress_percent = int((len(completed) / 2) * 100)
    db.commit()
    
    # Log progress to Proceedings
    log_readiness_proceeding(
        db,
        CURRENT_USER_ID,
        "Develop",
        f"Completed LMS lecture lesson (Lecture ID: {lecture_id}). Progress: {enr.progress_percent}%.",
        {"lms_progress": enr.progress_percent},
        "Continue completing LMS lessons to unlock certifications."
    )
    
    # Trigger Closed-loop Feedback
    process_feedback_loop_trigger(
        db, 
        CURRENT_USER_ID, 
        f"LMS Lesson Completion: Reached {enr.progress_percent}%", 
        enr.progress_percent
    )

    return {"progress_percent": enr.progress_percent}


@app.get("/api/lms/courses/{course_id}/posts", response_model=List[LmsCollaborationPostResponse])
def get_lms_collaboration_posts(course_id: int, db: Session = Depends(get_db)):
    posts = db.query(LmsCollaborationPost).filter(LmsCollaborationPost.course_id == course_id).order_by(LmsCollaborationPost.created_at.desc()).all()
    return [
        LmsCollaborationPostResponse(
            id=p.id,
            user_name=p.user_name,
            text=p.text,
            created_at=p.created_at
        )
        for p in posts
    ]


@app.post("/api/lms/courses/{course_id}/posts", response_model=LmsCollaborationPostResponse)
def create_lms_collaboration_post(course_id: int, payload: LmsPostRequest, db: Session = Depends(get_db)):
    p = LmsCollaborationPost(
        course_id=course_id,
        user_name="Learner_Fresh",
        text=payload.text
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return LmsCollaborationPostResponse(
        id=p.id,
        user_name=p.user_name,
        text=p.text,
        created_at=p.created_at
    )


# --- RAG / CAG / KNOWLEDGE GRAPH API ENDPOINTS ---
@app.get("/api/rag-cag/status")
def get_rag_cag_status(db: Session = Depends(get_db)):
    from app.services.readiness_engine import rag_cag_metrics
    docs_count = db.query(VectorDocument).count()
    caches_count = db.query(CagCacheRegistry).count()
    return {
        "vector_docs_count": docs_count,
        "cag_cached_docs_count": caches_count,
        "rag_status": "Enabled" if docs_count > 0 else "Disabled",
        "cag_status": "Pre-loaded in Model Context" if caches_count > 0 else "None",
        "latency_cag_ms": rag_cag_metrics["latency_cag_ms"],
        "latency_rag_ms": rag_cag_metrics["latency_rag_ms"],
        "cache_hits": rag_cag_metrics["cache_hits"]
    }


@app.get("/api/knowledge-graph")
def get_knowledge_graph(db: Session = Depends(get_db)):
    nodes = db.query(KnowledgeGraphNode).all()
    edges = db.query(KnowledgeGraphEdge).all()
    return {
        "nodes": [{"id": n.id, "type": n.node_type, "label": n.label} for n in nodes],
        "edges": [{"source": e.source_id, "target": e.target_id, "type": e.rel_type} for e in edges]
    }


# --- SAFETY & RESPONSIBLE AI QUEUES ENDPOINTS ---
@app.get("/api/safety/feedback-loops", response_model=List[FeedbackLoopResponse])
def get_feedback_loops(db: Session = Depends(get_db)):
    return db.query(FeedbackLoop).filter(FeedbackLoop.learner_id == CURRENT_USER_ID).all()


@app.get("/api/readiness/proceedings", response_model=List[ReadinessProceedingResponse])
def get_proceedings_timeline(db: Session = Depends(get_db)):
    # default entry if empty
    if db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID).count() == 0:
        db.add(ReadinessProceeding(
            learner_id=CURRENT_USER_ID,
            flow_stage="Dream",
            description="Created profile settings.",
            metrics_snapshot="{}",
            strategic_action="Attempt baseline diagnostic scorecard."
        ))
        db.commit()
    
    procs = db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID).order_by(ReadinessProceeding.created_at.desc(), ReadinessProceeding.id.desc()).all()
    results = []
    for p in procs:
        results.append(ReadinessProceedingResponse(
            id=p.id,
            flow_stage=p.flow_stage,
            description=p.description,
            metrics_snapshot=json.loads(p.metrics_snapshot),
            strategic_action=p.strategic_action,
            created_at=p.created_at
        ))
    return results


@app.get("/api/admin/hitl-queue", response_model=List[HitlQueueItemResponse])
def get_hitl_queue(db: Session = Depends(get_db)):
    query = db.query(
        HitlReviewQueue.id,
        HitlReviewQueue.learner_id,
        User.username.label("learner_name"),
        HitlReviewQueue.task_type,
        HitlReviewQueue.status,
        HitlReviewQueue.flag_reason,
        HitlReviewQueue.reviewer_notes,
        StudentCertification.title.label("certificate_title"),
        StudentCertification.issuer.label("issuer"),
        StudentCertification.credential_id.label("credential_id"),
        StudentCertification.file_url.label("file_url")
    ).outerjoin(
        User, User.id == HitlReviewQueue.learner_id
    ).outerjoin(
        StudentCertification, StudentCertification.id == HitlReviewQueue.reference_id
    ).all()
    
    result = []
    for row in query:
        result.append({
            "id": row.id,
            "learner_id": row.learner_id,
            "learner_name": row.learner_name,
            "task_type": row.task_type,
            "status": row.status,
            "flag_reason": row.flag_reason,
            "reviewer_notes": row.reviewer_notes,
            "certificate_title": row.certificate_title,
            "issuer": row.issuer,
            "credential_id": row.credential_id,
            "file_url": row.file_url
        })
    return result


@app.post("/api/admin/hitl-queue/{hitl_id}/resolve")
def resolve_hitl_task(hitl_id: int, decision: str = Form(...), reviewer_notes: str = Form(...), db: Session = Depends(get_db)):
    hitl = db.get(HitlReviewQueue, hitl_id)
    if not hitl:
        raise HTTPException(status_code=404, detail="Task not found")
    hitl.status = "Resolved"
    hitl.reviewer_notes = reviewer_notes

    if hitl.task_type == "Certification Review" and hitl.reference_id:
        cert = db.get(StudentCertification, hitl.reference_id)
        if cert:
            if decision == "approve":
                cert.verification_status = "Verified"
                if db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == hitl.learner_id, ReadinessProceeding.flow_stage == "Grow").count() == 0:
                    log_readiness_proceeding(db, hitl.learner_id, "Grow", f"Added verified credential: {cert.title}", {}, "Continue acquiring verified credentials.")
            elif decision == "reject":
                cert.verification_status = "Rejected"

    db.commit()
    return {"message": "Resolved"}


@app.get("/api/admin/roster", response_model=List[MentorRosterItemResponse])
def get_mentor_roster(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role == "Learner").all()
    
    # MVP specific: include CURRENT_USER_ID if they have learner data but aren't currently role="Learner"
    current_user = db.get(User, CURRENT_USER_ID)
    if current_user and current_user.role != "Learner":
        if db.query(LearnerProfile).filter(LearnerProfile.user_id == CURRENT_USER_ID).first():
            if not any(u.id == CURRENT_USER_ID for u in users):
                users.append(current_user)
    roster = []
    for user in users:
        profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
        scorecard = db.query(ReadinessScorecard).filter(ReadinessScorecard.learner_id == user.id).order_by(ReadinessScorecard.id.desc()).first()
        top_gap = db.query(GapReport).filter(GapReport.learner_id == user.id, GapReport.severity == "High").first()
        if not top_gap:
            top_gap = db.query(GapReport).filter(GapReport.learner_id == user.id).first()

        roster.append({
            "learner_id": user.id,
            "learner_name": user.username,
            "stream": profile.stream if profile else None,
            "target_role": profile.target_roles if profile else None,
            "cari": scorecard.CARI if scorecard else None,
            "readiness_level": scorecard.readiness_level if scorecard else None,
            "top_gap": top_gap.gap_type if top_gap else None
        })
    return roster


@app.get("/api/institution/analytics", response_model=InstitutionAnalyticsResponse)
def get_institution_analytics(db: Session = Depends(get_db)):
    import math

    users = db.query(User).filter(User.role == "Learner").all()
    current_user = db.get(User, CURRENT_USER_ID)
    if current_user and current_user.role != "Learner":
        if db.query(LearnerProfile).filter(LearnerProfile.user_id == CURRENT_USER_ID).first():
            if not any(u.id == CURRENT_USER_ID for u in users):
                users.append(current_user)

    total_scorecards = 0
    ready_count = 0
    total_scores = []
    
    purp_sum, comm_sum, dom_sum, port_sum = 0, 0, 0, 0

    learners_resp = []

    for user in users:
        profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
        scorecard = db.query(ReadinessScorecard).filter(ReadinessScorecard.learner_id == user.id).order_by(ReadinessScorecard.id.desc()).first()
        
        l_target = profile.target_roles if profile else None
        l_score = scorecard.total_score if scorecard else None
        l_status = scorecard.readiness_level if scorecard else None
        
        learners_resp.append({
            "learner_id": user.id,
            "learner_name": user.username,
            "target_role": l_target,
            "readiness_score": l_score,
            "readiness_status": l_status
        })
        
        if scorecard:
            total_scorecards += 1
            total_scores.append(scorecard.total_score)
            if scorecard.total_score >= 75:
                ready_count += 1
            purp_sum += scorecard.purpose_clarity
            comm_sum += scorecard.communication_readiness
            dom_sum += scorecard.domain_readiness
            port_sum += scorecard.portfolio_evidence

    # Calc ERR
    err = 0.0
    if total_scorecards > 0:
        err = round((ready_count / total_scorecards) * 100, 1)

    # Calc CSC
    csc = 0.0
    if len(total_scores) > 0:
        mean = sum(total_scores) / len(total_scores)
        variance = sum((x - mean) ** 2 for x in total_scores) / len(total_scores)
        csc = round(math.sqrt(variance), 1)

    # Calc SROI
    enrollments = db.query(LmsEnrollment).filter(LmsEnrollment.learner_id.in_([u.id for u in users])).all()
    sroi = 0.0
    if enrollments:
        sroi = round(sum(e.progress_percent for e in enrollments) / len(enrollments), 1)

    # Calc Gaps
    def get_status(val: float) -> str:
        if val >= 75: return "Pass"
        if val >= 40: return "Deficit"
        return "Severe Deficit"

    avg_purp = int(purp_sum / total_scorecards) if total_scorecards > 0 else 0
    avg_comm = int(comm_sum / total_scorecards) if total_scorecards > 0 else 0
    avg_dom = int(dom_sum / total_scorecards) if total_scorecards > 0 else 0
    avg_port = int(port_sum / total_scorecards) if total_scorecards > 0 else 0

    gaps = [
        {"name": "Purpose Clarity", "value": avg_purp, "status": get_status(avg_purp)},
        {"name": "Communication Readiness", "value": avg_comm, "status": get_status(avg_comm)},
        {"name": "Domain Technical Readiness", "value": avg_dom, "status": get_status(avg_dom)},
        {"name": "Portfolio Project Evidence", "value": avg_port, "status": get_status(avg_port)}
    ]

    return {
        "employment_readiness_rate": f"{err}%" if total_scorecards > 0 else "--",
        "cohort_skill_convergence": f"σ = {csc}" if total_scorecards > 0 else "--",
        "skilling_partner_roi": f"{sroi}%" if enrollments else "--",
        "competency_gaps": gaps,
        "cohort_size": len(users),
        "learners": learners_resp
    }


@app.get("/api/admin/learners/{learner_id}/diagnostics", response_model=MentorDiagnosticSnapshotResponse)
def get_learner_diagnostics(learner_id: int, db: Session = Depends(get_db)):
    user = db.get(User, learner_id)
    if not user:
        raise HTTPException(status_code=404, detail="Learner not found")
    if user.role != "Learner" and user.id != CURRENT_USER_ID:
        raise HTTPException(status_code=404, detail="Learner not found")

    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    scorecard = db.query(ReadinessScorecard).filter(ReadinessScorecard.learner_id == user.id).order_by(ReadinessScorecard.id.desc()).first()
    gaps = db.query(GapReport).filter(GapReport.learner_id == user.id).all()
    skills = db.query(StudentSkill).filter(StudentSkill.learner_id == user.id).all()

    scorecard_dict = None
    if scorecard:
        scorecard_dict = {
            "CARI": scorecard.CARI,
            "readiness_level": scorecard.readiness_level,
            "purpose_clarity": scorecard.purpose_clarity,
            "communication_readiness": scorecard.communication_readiness,
            "domain_readiness": scorecard.domain_readiness,
            "problem_solving": scorecard.problem_solving
        }

    return {
        "learner_id": user.id,
        "learner_name": user.username,
        "stream": profile.stream if profile else None,
        "target_roles": profile.target_roles if profile else None,
        "cari": scorecard.CARI if scorecard else None,
        "readiness_level": scorecard.readiness_level if scorecard else None,
        "scorecard": scorecard_dict,
        "gaps": [{"gap_type": g.gap_type, "severity": g.severity, "symptoms": g.symptoms} for g in gaps],
        "skills": [{"skill_name": s.name, "proficiency_level": s.proficiency} for s in skills]
    }



@app.get("/api/admin/security-logs", response_model=List[SecurityPolicyLogResponse])
def get_security_policy_logs(db: Session = Depends(get_db)):
    return db.query(SecurityPolicyLog).order_by(SecurityPolicyLog.created_at.desc()).all()


@app.get("/api/admin/moat")
def get_moat_metrics(db: Session = Depends(get_db)):
    moats = db.query(PlatformMoat).all()
    return {m.metric_key: m.metric_val for m in moats}


# --- MOCK INTERVIEW SUITE ROUTING LAYERS ---
from uuid import uuid4
import shutil

@app.post("/api/sessions", response_model=CreateSessionResponse)
def create_session(payload: CreateSessionRequest, db: Session = Depends(get_db)):
    interview_session = InterviewSession(
        user_name=payload.user_name.strip(),
        target_role=payload.target_role.strip(),
        experience_level=payload.experience_level.strip(),
        difficulty_level=(payload.difficulty or "medium").strip(),
        status="active",
    )
    db.add(interview_session)
    db.commit()
    db.refresh(interview_session)

    # Exposes Interview track to generator
    questions = generate_questions(
    payload.target_role,
    payload.experience_level,
    payload.difficulty,
    payload.interview_track
    )
    for idx, text in enumerate(questions, start=1):
        db.add(Question(session_id=interview_session.id, order_no=idx, text=text))

    db.commit()

    return CreateSessionResponse(session_id=interview_session.id, question_count=len(questions))


@app.get("/api/sessions/{session_id}", response_model=SessionSummary)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session_obj = db.get(InterviewSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionSummary(
        id=session_obj.id,
        user_name=session_obj.user_name,
        target_role=session_obj.target_role,
        experience_level=session_obj.experience_level,
        status=session_obj.status,
        difficulty=session_obj.difficulty_level,
    )


@app.get("/api/sessions/{session_id}/current-question", response_model=CurrentQuestionResponse)
def get_current_question(session_id: int, db: Session = Depends(get_db)):
    session_obj = db.get(InterviewSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    answered_question_ids = {
        row.question_id for row in db.scalars(
            select(Answer).where(Answer.session_id == session_id)
        ).all()
    }

    questions = db.scalars(
        select(Question).where(Question.session_id == session_id).order_by(Question.order_no.asc())
    ).all()

    for question in questions:
        if question.id not in answered_question_ids:
            return CurrentQuestionResponse(
                question_id=question.id,
                order_no=question.order_no,
                text=question.text,
                completed=False,
            )

    session_obj.status = "completed"
    db.commit()
    return CurrentQuestionResponse(completed=True)


@app.post("/api/sessions/{session_id}/answers", response_model=SubmitAnswerResponse)
def submit_answer(session_id: int, payload: SubmitAnswerRequest, db: Session = Depends(get_db)):
    session_obj = db.get(InterviewSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    question = db.get(Question, payload.question_id)
    if not question or question.session_id != session_id:
        raise HTTPException(status_code=404, detail="Question not found for session")

    existing = db.scalar(
        select(Answer).where(
            Answer.session_id == session_id,
            Answer.question_id == payload.question_id,
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Answer already submitted for this question")

    # Call evaluation with RAG context
    rag_ctx = query_rag_context(db, question.text)
    evaluation = evaluate_answer(
        question=question.text, 
        answer_text=payload.answer_text, 
        submitted_code=payload.submitted_code,
        rag_context=rag_ctx
    )

    answer = Answer(
        session_id=session_id,
        question_id=payload.question_id,
        answer_text=payload.answer_text.strip(),
        score_overall=evaluation.score_overall,
        score_clarity=evaluation.score_clarity,
        score_confidence=evaluation.score_confidence,
        filler_word_count=evaluation.filler_word_count,
        strengths="\n".join(evaluation.strengths),
        improvements="\n".join(evaluation.improvements),
        feedback=evaluation.feedback,
        submitted_code=payload.submitted_code,
        code_time_complexity=evaluation.code_time_complexity,
        code_space_complexity=evaluation.code_space_complexity,
        code_cleanliness_score=evaluation.code_cleanliness_score,
        code_error_resilience=evaluation.code_error_resilience,
        code_syntax_passes=evaluation.code_syntax_passes,
        technical_fluency=evaluation.technical_fluency,
        non_technical_communication=evaluation.non_technical_communication,
        growth_mindset=evaluation.growth_mindset,
        ownership=evaluation.ownership,
        collaborative_empathy=evaluation.collaborative_empathy,
        stress_resilience=evaluation.stress_resilience,
        professional_integrity=evaluation.professional_integrity
    )
    db.add(answer)
    db.commit()

    next_q = get_current_question(session_id, db)
    
    # Process feedback loops check
    process_feedback_loop_trigger(db, CURRENT_USER_ID, f"Interview Mock Answer submission.", evaluation.score_overall)

    return SubmitAnswerResponse(
        saved=True,
        answer_id=answer.id,
        evaluation=AnswerEvaluation(
            score_overall=evaluation.score_overall,
            score_clarity=evaluation.score_clarity,
            score_confidence=evaluation.score_confidence,
            filler_word_count=evaluation.filler_word_count,
            strengths=evaluation.strengths,
            improvements=evaluation.improvements,
            feedback=evaluation.feedback,
            code_time_complexity=evaluation.code_time_complexity,
            code_space_complexity=evaluation.code_space_complexity,
            code_cleanliness_score=evaluation.code_cleanliness_score,
            code_error_resilience=evaluation.code_error_resilience,
            code_syntax_passes=evaluation.code_syntax_passes,
            technical_fluency=evaluation.technical_fluency,
            non_technical_communication=evaluation.non_technical_communication,
            growth_mindset=evaluation.growth_mindset,
            ownership=evaluation.ownership,
            collaborative_empathy=evaluation.collaborative_empathy,
            stress_resilience=evaluation.stress_resilience,
            professional_integrity=evaluation.professional_integrity
        ),
        next_question_available=not next_q.completed,
    )


@app.post("/api/sessions/{session_id}/answers/media", response_model=SubmitAnswerResponse)
def submit_media_answer(
    session_id: int,
    question_id: int = Form(...),
    media_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    session_obj = db.get(InterviewSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    question = db.get(Question, question_id)
    if not question or question.session_id != session_id:
        raise HTTPException(status_code=404, detail="Question not found for session")

    existing = db.scalar(
        select(Answer).where(
            Answer.session_id == session_id,
            Answer.question_id == question_id,
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Answer already submitted for this question")

    if media_type not in {"audio", "video"}:
        raise HTTPException(status_code=400, detail="Media type must be either 'audio' or 'video'.")

    try:
        file_path, media_url = save_media_file(session_id, question_id, file, media_type)
        transcription = transcribe_media(file_path) if has_openai() else ""
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Media processing failed: {str(exc)}")

    answer_text = transcription.strip() or f"Recorded {media_type} response uploaded."
    
    rag_ctx = query_rag_context(db, question.text)
    evaluation = evaluate_answer(question=question.text, answer_text=answer_text, rag_context=rag_ctx)

    answer = Answer(
        session_id=session_id,
        question_id=question_id,
        answer_text=answer_text,
        score_overall=evaluation.score_overall,
        score_clarity=evaluation.score_clarity,
        score_confidence=evaluation.score_confidence,
        filler_word_count=evaluation.filler_word_count,
        strengths="\n".join(evaluation.strengths),
        improvements="\n".join(evaluation.improvements),
        feedback=evaluation.feedback,
        submitted_code=None,
        code_time_complexity=None,
        code_space_complexity=None,
        code_cleanliness_score=None,
        code_error_resilience=None,
        code_syntax_passes=None,
        technical_fluency=evaluation.technical_fluency,
        non_technical_communication=evaluation.non_technical_communication,
        growth_mindset=evaluation.growth_mindset,
        ownership=evaluation.ownership,
        collaborative_empathy=evaluation.collaborative_empathy,
        stress_resilience=evaluation.stress_resilience,
        professional_integrity=evaluation.professional_integrity
    )

    media = MediaAsset(
        answer=answer,
        media_type=media_type,
        file_name=os.path.basename(file_path),
        file_url=media_url,
        transcription_text=transcription.strip() or None,
        duration_seconds=None,
        byte_size=os.path.getsize(file_path),
        playback_count=0,
    )

    db.add(answer)
    db.add(media)
    db.commit()
    db.refresh(answer)
    db.refresh(media)

    next_q = get_current_question(session_id, db)

    media_info = MediaInfo(
        media_type=media.media_type,
        media_url=media.file_url,
        transcription=media.transcription_text,
        duration_seconds=media.duration_seconds,
        byte_size=media.byte_size,
        playback_count=media.playback_count,
    )

    return SubmitAnswerResponse(
        saved=True,
        answer_id=answer.id,
        evaluation=AnswerEvaluation(
            score_overall=evaluation.score_overall,
            score_clarity=evaluation.score_clarity,
            score_confidence=evaluation.score_confidence,
            filler_word_count=evaluation.filler_word_count,
            strengths=evaluation.strengths,
            improvements=evaluation.improvements,
            feedback=evaluation.feedback,
            code_time_complexity=evaluation.code_time_complexity,
            code_space_complexity=evaluation.code_space_complexity,
            code_cleanliness_score=evaluation.code_cleanliness_score,
            code_error_resilience=evaluation.code_error_resilience,
            code_syntax_passes=evaluation.code_syntax_passes,
            technical_fluency=evaluation.technical_fluency,
            non_technical_communication=evaluation.non_technical_communication,
            growth_mindset=evaluation.growth_mindset,
            ownership=evaluation.ownership,
            collaborative_empathy=evaluation.collaborative_empathy,
            stress_resilience=evaluation.stress_resilience,
            professional_integrity=evaluation.professional_integrity
        ),
        next_question_available=not next_q.completed,
        transcription=transcription.strip() or None,
        media=media_info,
    )


@app.post("/api/sessions/{session_id}/answers/{answer_id}/media/analytics")
def record_media_analytics(
    session_id: int,
    answer_id: int,
    payload: MediaAnalyticsRequest,
    db: Session = Depends(get_db),
):
    answer = db.get(Answer, answer_id)
    if not answer or answer.session_id != session_id:
        raise HTTPException(status_code=404, detail="Answer not found for session")
    if not answer.media:
        raise HTTPException(status_code=404, detail="Media asset not found for answer")

    if payload.playback_event == "playback":
        answer.media.playback_count += 1
        db.commit()

    return {"playback_count": answer.media.playback_count}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    await websocket.accept()
    sid = str(session_id)
    conns = _session_connections.setdefault(sid, set())
    conns.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except Exception:
                payload = {"type": "message", "data": data}

            typ = payload.get("type")
            if typ == "start_timer":
                seconds = int(payload.get("seconds", 30))

                task = _session_timer_tasks.get(sid)
                if task and not task.done():
                    task.cancel()

                async def _run_timer(sid_inner: str, secs: int):
                    try:
                        for remaining in range(secs, -1, -1):
                            await _broadcast(int(sid_inner), {"type": "tick", "remaining": remaining})
                            await asyncio.sleep(1)
                        await _broadcast(int(sid_inner), {"type": "ended"})
                    except asyncio.CancelledError:
                        await _broadcast(int(sid_inner), {"type": "stopped"})

                task = asyncio.create_task(_run_timer(sid, seconds))
                _session_timer_tasks[sid] = task
                await websocket.send_text(json.dumps({"type": "started", "seconds": seconds}))

            elif typ == "stop_timer":
                task = _session_timer_tasks.get(sid)
                if task and not task.done():
                    task.cancel()
                await websocket.send_text(json.dumps({"type": "stopped"}))

            else:
                await websocket.send_text(json.dumps({"type": "echo", "payload": payload}))
    except WebSocketDisconnect:
        conns.discard(websocket)
        return


@app.get("/api/sessions/{session_id}/report", response_model=ReportResponse)
def get_report(session_id: int, db: Session = Depends(get_db)):
    session_obj = db.get(InterviewSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    questions = db.scalars(
        select(Question).where(Question.session_id == session_id).order_by(Question.order_no.asc())
    ).all()
    answers = db.scalars(
        select(Answer).where(Answer.session_id == session_id).order_by(Answer.id.asc())
    ).all()

    answer_map = {a.question_id: a for a in answers}
    items = []

    overall_scores = []
    clarity_scores = []
    confidence_scores = []
    total_fillers = 0
    strengths_acc = []
    improvements_acc = []

    for q in questions:
        ans = answer_map.get(q.id)
        if not ans:
            continue
        strengths = [s for s in ans.strengths.split("\n") if s.strip()]
        improvements = [s for s in ans.improvements.split("\n") if s.strip()]
        media_info = None
        if ans.media:
            media_info = MediaInfo(
                media_type=ans.media.media_type,
                media_url=ans.media.file_url,
                transcription=ans.media.transcription_text,
                duration_seconds=ans.media.duration_seconds,
                byte_size=ans.media.byte_size,
                playback_count=ans.media.playback_count,
            )
        items.append(
            ReportItem(
                question=q.text,
                answer=ans.answer_text,
                answer_id=ans.id,
                score_overall=ans.score_overall,
                score_clarity=ans.score_clarity,
                score_confidence=ans.score_confidence,
                filler_word_count=ans.filler_word_count,
                strengths=strengths,
                improvements=improvements,
                feedback=ans.feedback,
                media=media_info,
                submitted_code=ans.submitted_code,
                code_time_complexity=ans.code_time_complexity,
                code_space_complexity=ans.code_space_complexity,
                code_cleanliness_score=ans.code_cleanliness_score,
                code_error_resilience=ans.code_error_resilience,
                code_syntax_passes=ans.code_syntax_passes,
                technical_fluency=ans.technical_fluency,
                non_technical_communication=ans.non_technical_communication,
                growth_mindset=ans.growth_mindset,
                ownership=ans.ownership,
                collaborative_empathy=ans.collaborative_empathy,
                stress_resilience=ans.stress_resilience,
                professional_integrity=ans.professional_integrity
            )
        )
        overall_scores.append(ans.score_overall)
        clarity_scores.append(ans.score_clarity)
        confidence_scores.append(ans.score_confidence)
        total_fillers += ans.filler_word_count
        strengths_acc.extend(strengths)
        improvements_acc.extend(improvements)

    def dedupe(items_: list[str]) -> list[str]:
        seen = set()
        result = []
        for item in items_:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(item.strip())
        return result

    strengths_summary = dedupe(strengths_acc)[:5] or ["Shows willingness to participate."]
    improvement_summary = dedupe(improvements_acc)[:5] or ["Continue practicing concise answers."]
    next_steps = [
        "Practice STAR-based answers for behavioral questions.",
        "Solve complexity refactoring exercises on technical tracks.",
        "Add try-except resilient blocks to coding tasks.",
        "Improve confidence scores by reducing filler words."
    ]

    avg_overall = round(sum(overall_scores) / len(overall_scores)) if overall_scores else 0
    avg_clarity = round(sum(clarity_scores) / len(clarity_scores)) if clarity_scores else 0
    avg_confidence = round(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0

    if session_obj.status == "Completed" and db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID, ReadinessProceeding.flow_stage == "Demonstrate").count() == 0:
        log_readiness_proceeding(db, CURRENT_USER_ID, "Demonstrate", f"Generated Mock Interview report (Score: {avg_overall}).", {"score": avg_overall}, "Review interview feedback and improve.")

    return ReportResponse(
        session_id=session_obj.id,
        user_name=session_obj.user_name,
        target_role=session_obj.target_role,
        experience_level=session_obj.experience_level,
        difficulty=session_obj.difficulty_level,
        overall_score=avg_overall,
        clarity_score=avg_clarity,
        confidence_score=avg_confidence,
        total_filler_words=total_fillers,
        status=session_obj.status,
        strengths_summary=strengths_summary,
        improvement_summary=improvement_summary,
        recommended_next_steps=next_steps,
        items=items,
    )


# --- EMPLOYER BOARD ENDPOINTS ---
@app.get("/api/employer/matches", response_model=List[EmployerMatchResponse])
def get_employer_matches(db: Session = Depends(get_db)):
    current_user = db.get(User, CURRENT_USER_ID)
    if not current_user or current_user.role not in ["Employer", "Admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view candidates")
        
    learners = db.query(User).filter(User.role == "Learner").all()
    
    # For MVP demo: Include current user if they have a LearnerProfile even if Admin/Employer
    if current_user and current_user.role != "Learner":
        if db.query(LearnerProfile).filter(LearnerProfile.user_id == CURRENT_USER_ID).first():
            if not any(u.id == CURRENT_USER_ID for u in learners):
                learners.append(current_user)
                
    jobs = db.query(ExistingJob).all()
    
    results = []
    
    for learner in learners:
        profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == learner.id).first()
        if not profile:
            continue
            
        student_skills = db.query(StudentSkill).filter(StudentSkill.learner_id == learner.id).all()
        student_skill_names = {s.name.strip().lower() for s in student_skills if s.name}
        
        best_match = 0
        best_matched_skills = []
        
        if jobs:
            for j in jobs:
                req_skills = [s.strip() for s in j.required_skills.split(",") if s.strip()]
                matched = []
                for rs in req_skills:
                    if any(rs.lower() in ss for ss in student_skill_names):
                        matched.append(rs)
                
                score = round((len(matched) / len(req_skills)) * 100) if req_skills else 0
                if score >= best_match:
                    best_match = score
                    best_matched_skills = matched
        
        results.append(
            EmployerMatchResponse(
                learner_id=learner.id,
                candidate_name=learner.username,
                target_role=profile.target_roles or "Unspecified",
                stream=profile.stream or "Unspecified",
                armc_score=best_match,
                matched_skills=best_matched_skills
            )
        )
        
    results.sort(key=lambda x: x.armc_score, reverse=True)
    return results

@app.get("/api/employer/portfolio/{learner_id}/download")
def download_learner_portfolio(learner_id: int, db: Session = Depends(get_db)):
    current_user = db.get(User, CURRENT_USER_ID)
    if not current_user or current_user.role not in ["Employer", "Admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to download portfolio")
        
    learner = db.get(User, learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == learner.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
        
    skills = db.query(StudentSkill).filter(StudentSkill.learner_id == learner_id).all()
    certs = db.query(StudentCertification).filter(StudentCertification.learner_id == learner_id).all()
    scorecard = db.query(ReadinessScorecard).filter(ReadinessScorecard.learner_id == learner_id).order_by(ReadinessScorecard.id.desc()).first()
    lms = db.query(LmsEnrollment).filter(LmsEnrollment.learner_id == learner_id).all()
    
    md = []
    md.append(f"# Professional Portfolio: {learner.username}")
    md.append(f"**Target Role:** {profile.target_roles or 'Unspecified'}")
    md.append(f"**Stream:** {profile.stream or 'Unspecified'}")
    md.append(f"**Experience:** {profile.experience_level or 'Unspecified'}")
    md.append("\n---")
    
    md.append("\n## Professional Skills")
    if skills:
        for s in skills:
            md.append(f"- **{s.name}** ({s.proficiency}) - Verified: {'Yes' if s.verification_status == 'Verified' else 'No'}")
    else:
        md.append("- No skills listed.")
        
    md.append("\n## Certifications")
    if certs:
        for c in certs:
            status = "Verified" if c.verification_status == "Verified" else "Pending/Unverified"
            md.append(f"- **{c.title}** ({c.issuer}) - {status}")
    else:
        md.append("- No certifications listed.")
        
    md.append("\n## LMS Progress")
    if lms:
        for e in lms:
            md.append(f"- Course ID {e.course_id}: {e.progress_percent}% Complete")
    else:
        md.append("- No LMS records.")
        
    if scorecard:
        md.append("\n## Aggregate Readiness Assessment")
        md.append(f"- **Overall Readiness Score:** {scorecard.total_score}/100 ({scorecard.readiness_level})")
        md.append(f"- **CARI Index:** {scorecard.CARI}")
        md.append(f"- **Technical/Domain Readiness:** {scorecard.domain_readiness}/100")
        md.append(f"- **Communication Readiness:** {scorecard.communication_readiness}/100")
        
    content = "\n".join(md)
    headers = {
        "Content-Disposition": f"attachment; filename=candidate_{learner_id}_portfolio.md"
    }
    return Response(content=content, media_type="text/markdown", headers=headers)

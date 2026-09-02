from pathlib import Path
import os
import time
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form
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
    MentorshipSessionResponse,
    SecurityPolicyLogResponse,
    FeedbackLoopResponse,
    PlatformMoatResponse,
    ReadinessProceedingResponse,
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

        # Rate-limit per IP + API endpoint.
        rate_key = f"{client_ip}:{request.url.path}"

        last_time = _rate_limits.get(rate_key, 0)

        # Block only extremely rapid repeated requests
        # to the SAME endpoint.
        if curr_time - last_time < 0.01:
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
def switch_active_role(role: str, db: Session = Depends(get_db)):
    global CURRENT_USER_ID
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
def framework_details():
    return get_platform_framework()


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

    # Log to proceedings audit ledger
    log_readiness_proceeding(
        db,
        CURRENT_USER_ID,
        "Diagnose",
        "Completed comprehensive diagnostic assessment.",
        {"total_score": scorecard["total_score"], "CARI": scorecard["CARI"], "CCQ": scorecard["CCQ"]},
        diag["next_best_action"]
    )
    
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
def add_learner_skill(payload: StudentSkillRequest, db: Session = Depends(get_db)):
    skill = StudentSkill(
        learner_id=CURRENT_USER_ID,
        name=payload.name,
        category=payload.category,
        proficiency=payload.proficiency,
        verification_status="Self-Reported"
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@app.get("/api/learner/certifications", response_model=List[StudentCertificationResponse])
def get_learner_certifications(db: Session = Depends(get_db)):
    return db.query(StudentCertification).filter(StudentCertification.learner_id == CURRENT_USER_ID).all()


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
        verification_status="Verified",  # Auto verified mock status
        file_url=file_url
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
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
    meet_url = f"https://meet.google.com/mock-{uuid4().hex[:4]}-{uuid4().hex[:4]}"
    session = MentorSession(
        learner_id=CURRENT_USER_ID,
        mentor_name=payload.mentor_name,
        date_str=payload.date_str,
        time_str=payload.time_str,
        meet_url=meet_url,
        notes="Scheduled via AspireOS dashboard.",
        status="Scheduled"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


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
            if skill.lower() in student_skill_names:
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
    docs_count = db.query(VectorDocument).count()
    caches_count = db.query(CagCacheRegistry).count()
    return {
        "vector_docs_count": docs_count,
        "cag_cached_docs_count": caches_count,
        "rag_status": "Enabled" if docs_count > 0 else "Disabled",
        "cag_status": "Pre-loaded in Model Context" if caches_count > 0 else "None",
        "latency_cag_ms": 12,
        "latency_rag_ms": 280,
        "cache_hits": 45
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
    
    procs = db.query(ReadinessProceeding).filter(ReadinessProceeding.learner_id == CURRENT_USER_ID).order_by(ReadinessProceeding.created_at.desc()).all()
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


@app.get("/api/admin/hitl-queue")
def get_hitl_queue(db: Session = Depends(get_db)):
    return db.query(HitlReviewQueue).all()


@app.post("/api/admin/hitl-queue/{hitl_id}/resolve")
def resolve_hitl_task(hitl_id: int, reviewer_notes: str = Form(...), db: Session = Depends(get_db)):
    hitl = db.get(HitlReviewQueue, hitl_id)
    if not hitl:
        raise HTTPException(status_code=404, detail="Task not found")
    hitl.status = "Resolved"
    hitl.reviewer_notes = reviewer_notes
    db.commit()
    return {"message": "Resolved"}


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

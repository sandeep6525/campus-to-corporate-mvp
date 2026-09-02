from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, func, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base
from .encryption import EncryptedString


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(40), default="Learner")  # Learner, Mentor, Institution, Employer
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    stream: Mapped[str] = mapped_column(String(120), default="Engineering and Technology")
    experience_level: Mapped[str] = mapped_column(String(60), default="Fresher")
    location: Mapped[str] = mapped_column(String(120), default="Global")
    dream_statement: Mapped[str] = mapped_column(EncryptedString, nullable=True)
    purpose_statement: Mapped[str] = mapped_column(EncryptedString, nullable=True)
    strengths: Mapped[str] = mapped_column(EncryptedString, nullable=True)
    fears: Mapped[str] = mapped_column(EncryptedString, nullable=True)
    target_roles: Mapped[str] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(40), default="Global")
    language: Mapped[str] = mapped_column(String(40), default="English")


class ContextFactors(Base):
    __tablename__ = "context_factors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    family_pressure: Mapped[str] = mapped_column(String(40), default="Medium")  # Low, Medium, High
    financial_dependency: Mapped[str] = mapped_column(String(40), default="Yes")  # Yes, No
    confidence_baseline: Mapped[int] = mapped_column(Integer, default=50)
    stress_baseline: Mapped[int] = mapped_column(Integer, default=50)
    resilience_rating: Mapped[int] = mapped_column(Integer, default=50)
    income_tier: Mapped[str] = mapped_column(String(40), default="Middle Class")  # Low, Middle, High
    city_tier: Mapped[str] = mapped_column(String(40), default="Tier 2")  # Tier 1, Tier 2, Tier 3, Rural
    college_tier: Mapped[str] = mapped_column(String(40), default="Tier 2")  # Tier 1, Tier 2, Tier 3


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))  # Technical, Non-Technical
    proficiency: Mapped[str] = mapped_column(String(40), default="Intermediate")  # Beginner, Intermediate, Advanced
    verification_status: Mapped[str] = mapped_column(String(40), default="Self-Reported")  # Self-Reported, AI-Verified, Mentor-Approved


class StudentCertification(Base):
    __tablename__ = "student_certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(120))
    issuer: Mapped[str] = mapped_column(String(120))
    issue_date: Mapped[str] = mapped_column(String(40), nullable=True)
    credential_id: Mapped[str] = mapped_column(String(120), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(40), default="Pending")  # Pending, Verified, Flagged
    file_url: Mapped[str] = mapped_column(String(500), nullable=True)


class StudentLink(Base):
    __tablename__ = "student_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    github_url: Mapped[str] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str] = mapped_column(String(500), nullable=True)
    leetcode_url: Mapped[str] = mapped_column(String(500), nullable=True)


class CareerShiftMatrix(Base):
    __tablename__ = "career_shift_matrices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    shift_reason: Mapped[str] = mapped_column(Text)
    capability_delta_json: Mapped[str] = mapped_column(Text)  # JSON holding transferable skills, gaps, next steps


class DreamPathway(Base):
    __tablename__ = "dream_pathways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    target_role: Mapped[str] = mapped_column(String(120))
    stream: Mapped[str] = mapped_column(String(120))
    growth_3yr: Mapped[str] = mapped_column(Text, nullable=True)
    growth_5yr: Mapped[str] = mapped_column(Text, nullable=True)
    growth_10yr: Mapped[str] = mapped_column(Text, nullable=True)
    available_jobs_count: Mapped[int] = mapped_column(Integer, default=0)
    future_jobs_count: Mapped[int] = mapped_column(Integer, default=0)
    skill_gaps_count: Mapped[int] = mapped_column(Integer, default=0)


class ReadinessScorecard(Base):
    __tablename__ = "readiness_scorecards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    purpose_clarity: Mapped[int] = mapped_column(Integer, default=50)
    self_awareness_confidence: Mapped[int] = mapped_column(Integer, default=50)
    communication_readiness: Mapped[int] = mapped_column(Integer, default=50)
    digital_ai_readiness: Mapped[int] = mapped_column(Integer, default=50)
    domain_readiness: Mapped[int] = mapped_column(Integer, default=50)
    problem_solving: Mapped[int] = mapped_column(Integer, default=50)
    collaboration_leadership: Mapped[int] = mapped_column(Integer, default=50)
    career_readiness: Mapped[int] = mapped_column(Integer, default=50)
    portfolio_evidence: Mapped[int] = mapped_column(Integer, default=50)
    total_score: Mapped[int] = mapped_column(Integer, default=50)
    readiness_level: Mapped[str] = mapped_column(String(40), default="Emerging")
    CARI: Mapped[int] = mapped_column(Integer, default=50)  # Context-Adjusted Readiness Index
    CCQ: Mapped[int] = mapped_column(Integer, default=50)   # Contextual Challenge Quotient
    resilience_index: Mapped[int] = mapped_column(Integer, default=50)
    assessment_type: Mapped[str] = mapped_column(String(40), default="Baseline")  # Baseline, Current
    cgi: Mapped[int] = mapped_column(Integer, default=0)    # Confidence Gain Index
    rv: Mapped[int] = mapped_column(Integer, default=0)     # Remediation Velocity (days to fix gaps)
    pcs: Mapped[int] = mapped_column(Integer, default=0)    # Portfolio Completeness Score
    success_mantras_progress: Mapped[int] = mapped_column(Integer, default=0) # mantras completed %
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GapReport(Base):
    __tablename__ = "gap_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    gap_type: Mapped[str] = mapped_column(String(120))
    symptoms: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(40), default="Medium")  # Low, Medium, High
    priority: Mapped[int] = mapped_column(Integer, default=50)
    recommended_fix: Mapped[str] = mapped_column(Text)
    evidence_required: Mapped[str] = mapped_column(String(120))


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    plan_type: Mapped[str] = mapped_column(String(40), default="30-60-90 Day Plan")
    weekly_tasks_json: Mapped[str] = mapped_column(Text)  # JSON holds tasks and statuses
    recommended_courses_json: Mapped[str] = mapped_column(Text, nullable=True)
    recommended_projects_json: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Active")


class SuccessMantra(Base):
    __tablename__ = "success_mantras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))  # Interview, Portfolio, Digital, Soft Skills
    content: Mapped[str] = mapped_column(Text)
    action_items: Mapped[str] = mapped_column(Text)  # Bulleted tasks


class CampusCourse(Base):
    __tablename__ = "campus_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(120))  # IIT-Bombay, Stanford, local, etc.
    tier: Mapped[str] = mapped_column(String(40), default="Tier 2")  # Tier 1, Tier 2, Tier 3
    origin: Mapped[str] = mapped_column(String(40), default="India")  # India, Abroad
    direct_url: Mapped[str] = mapped_column(String(500))
    fee_type: Mapped[str] = mapped_column(String(40), default="Free")  # Free, Paid


class CourseCoupon(Base):
    __tablename__ = "course_coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(40))
    organization: Mapped[str] = mapped_column(String(120), default="Asperion Partnership")
    discount_percent: Mapped[int] = mapped_column(Integer, default=100)


class LmsCourse(Base):
    __tablename__ = "lms_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    instructor: Mapped[str] = mapped_column(String(120), default="Asperion Faculty")
    stream: Mapped[str] = mapped_column(String(120))
    duration: Mapped[str] = mapped_column(String(40), default="4 weeks")
    difficulty: Mapped[str] = mapped_column(String(40), default="Medium")


class LmsModule(Base):
    __tablename__ = "lms_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(200))
    order_no: Mapped[int] = mapped_column(Integer)


class LmsLecture(Base):
    __tablename__ = "lms_lectures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(200))
    content_type: Mapped[str] = mapped_column(String(40), default="Text")  # Text, Video, Worksheet, Mantra
    content: Mapped[str] = mapped_column(Text)
    mantras: Mapped[str | None] = mapped_column(Text, nullable=True)


class LmsEnrollment(Base):
    __tablename__ = "lms_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    course_id: Mapped[int] = mapped_column(Integer, index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    completed_lectures_json: Mapped[str] = mapped_column(Text, default="[]")


class LmsCollaborationPost(Base):
    __tablename__ = "lms_collaboration_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, index=True)
    user_name: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExistingJob(Base):
    __tablename__ = "existing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120))
    organization: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(60), default="Corporate")  # Government, Corporate, Local, National, International
    required_skills: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500))
    match_score: Mapped[int] = mapped_column(Integer, default=50)


class InstitutionalCollaboration(Base):
    __tablename__ = "institutional_collaborations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    partner_name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(60), default="Public")  # Public, Private
    skilling_program: Mapped[str] = mapped_column(String(200))
    structural_gaps: Mapped[str] = mapped_column(Text)
    SROI: Mapped[int] = mapped_column(Integer, default=70)  # Skilling Partner ROI
    CSC: Mapped[int] = mapped_column(Integer, default=15)   # Cohort Skill Convergence


class KnowledgeGraphNode(Base):
    __tablename__ = "knowledge_graph_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_type: Mapped[str] = mapped_column(String(40))  # Dream, Skill, Course, Coupon, Job
    label: Mapped[str] = mapped_column(String(120))


class KnowledgeGraphEdge(Base):
    __tablename__ = "knowledge_graph_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(Integer)
    target_id: Mapped[int] = mapped_column(Integer)
    rel_type: Mapped[str] = mapped_column(String(60))  # requires, remediates, discounted_by, matches


class VectorDocument(Base):
    __tablename__ = "vector_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)


class CagCacheRegistry(Base):
    __tablename__ = "cag_cache_registries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doc_title: Mapped[str] = mapped_column(String(200))
    cache_status: Mapped[str] = mapped_column(String(40), default="Pre-cached")


class FeedbackLoop(Base):
    __tablename__ = "feedback_loops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    trigger_event: Mapped[str] = mapped_column(String(200))
    action_taken: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="Active")  # Active, Resolved
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AiAuditLog(Base):
    __tablename__ = "ai_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(120))
    prompt: Mapped[str] = mapped_column(Text)
    output: Mapped[str] = mapped_column(Text)
    safety_score: Mapped[str] = mapped_column(String(40), default="Safe")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HitlReviewQueue(Base):
    __tablename__ = "hitl_review_queues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    task_type: Mapped[str] = mapped_column(String(120))  # final certification, disputed score, safety warning
    flag_reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="Pending")  # Pending, Resolved
    reviewer_notes: Mapped[str] = mapped_column(Text, default="")
    resolved_at: Mapped[str] = mapped_column(String(60), nullable=True)


class PlatformMoat(Base):
    __tablename__ = "platform_moats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    metric_key: Mapped[str] = mapped_column(String(120))
    metric_val: Mapped[str] = mapped_column(String(120))


class SecurityPolicyLog(Base):
    __tablename__ = "security_policy_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(120))  # Authentication, Mime Type Validation, Rate Limit, Prompt Bypass
    action_attempt: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="Allowed")  # Allowed, Blocked, Warned
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReadinessProceeding(Base):
    __tablename__ = "readiness_proceedings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    flow_stage: Mapped[str] = mapped_column(String(40))  # Dream, Discover, Diagnose, Design, etc.
    description: Mapped[str] = mapped_column(Text)
    metrics_snapshot: Mapped[str] = mapped_column(Text)  # JSON snapshot of current metrics
    strategic_action: Mapped[str] = mapped_column(Text)  # Next steps recommended
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MentorSession(Base):
    __tablename__ = "mentor_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    mentor_name: Mapped[str] = mapped_column(String(120))
    date_str: Mapped[str] = mapped_column(String(60))
    time_str: Mapped[str] = mapped_column(String(60))
    meeting_type: Mapped[str | None] = mapped_column(String(60), nullable=True, default="Google Meet")
    meeting_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    meet_url: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str] = mapped_column(Text, default="")
    feedback: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="Scheduled")  # Scheduled, Completed, Cancelled


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_name: Mapped[str] = mapped_column(String(120))
    target_role: Mapped[str] = mapped_column(String(120))
    experience_level: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30), default="active")
    difficulty_level: Mapped[str] = mapped_column(String(30), default="medium")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    questions: Mapped[list["Question"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    answers: Mapped[list["Answer"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    order_no: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    session: Mapped["Session"] = relationship(back_populates="questions")


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    answer_text: Mapped[str] = mapped_column(Text)

    score_overall: Mapped[int] = mapped_column(Integer)
    score_clarity: Mapped[int] = mapped_column(Integer)
    score_confidence: Mapped[int] = mapped_column(Integer)
    filler_word_count: Mapped[int] = mapped_column(Integer)
    strengths: Mapped[str] = mapped_column(Text)
    improvements: Mapped[str] = mapped_column(Text)
    feedback: Mapped[str] = mapped_column(Text)

    # Technical Capabilities & Coding assessments
    submitted_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    code_time_complexity: Mapped[str | None] = mapped_column(String(60), nullable=True)
    code_space_complexity: Mapped[str | None] = mapped_column(String(60), nullable=True)
    code_cleanliness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code_error_resilience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code_syntax_passes: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Skills sub-scores
    technical_fluency: Mapped[int] = mapped_column(Integer, default=50)
    non_technical_communication: Mapped[int] = mapped_column(Integer, default=50)

    # Behavioral & Attitude metrics
    growth_mindset: Mapped[int] = mapped_column(Integer, default=50)
    ownership: Mapped[int] = mapped_column(Integer, default=50)
    collaborative_empathy: Mapped[int] = mapped_column(Integer, default=50)
    stress_resilience: Mapped[int] = mapped_column(Integer, default=50)
    professional_integrity: Mapped[int] = mapped_column(Integer, default=50)

    session: Mapped["Session"] = relationship(back_populates="answers")
    media: Mapped["MediaAsset | None"] = relationship(back_populates="answer", uselist=False)


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.id"), unique=True)
    media_type: Mapped[str] = mapped_column(String(40))
    file_name: Mapped[str] = mapped_column(String(260))
    file_url: Mapped[str] = mapped_column(String(500))
    transcription_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    byte_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    playback_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    answer: Mapped["Answer"] = relationship(back_populates="media")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(Integer, index=True)
    job_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(40), default="Applied")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


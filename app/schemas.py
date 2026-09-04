from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any

class CreateSessionRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=120)
    target_role: str = Field(min_length=1, max_length=120)
    experience_level: str = Field(min_length=1, max_length=60)
    difficulty: str = Field(default="medium")
    interview_track: str = Field(default="HR & Behavioral")
    interviewer_avatar: str = Field(default="Sophia")


class CreateSessionResponse(BaseModel):
    session_id: int
    question_count: int


class SessionSummary(BaseModel):
    id: int
    user_name: str
    target_role: str
    experience_level: str
    status: str
    difficulty: str | None = None
    interviewer_avatar: str | None = None


class CurrentQuestionResponse(BaseModel):
    question_id: int | None = None
    order_no: int | None = None
    text: str | None = None
    completed: bool = False


class SubmitAnswerRequest(BaseModel):
    question_id: int
    answer_text: str = Field(min_length=1)
    submitted_code: str | None = None


class AnswerEvaluation(BaseModel):
    score_overall: int
    score_clarity: int
    score_confidence: int
    filler_word_count: int
    strengths: List[str]
    improvements: List[str]
    feedback: str
    
    # Coding and complexity evaluation
    code_time_complexity: str | None = None
    code_space_complexity: str | None = None
    code_cleanliness_score: int | None = None
    code_error_resilience: int | None = None
    code_syntax_passes: bool | None = None

    # Technical Fluency & Communication sub-scores
    technical_fluency: int = 50
    non_technical_communication: int = 50

    # Behavioral & Attitude metrics
    growth_mindset: int = 50
    ownership: int = 50
    collaborative_empathy: int = 50
    stress_resilience: int = 50
    professional_integrity: int = 50


class MediaInfo(BaseModel):
    media_type: str
    media_url: str
    transcription: str | None = None
    duration_seconds: int | None = None
    byte_size: int | None = None
    playback_count: int = 0


class SubmitAnswerResponse(BaseModel):
    saved: bool
    answer_id: int | None = None
    evaluation: AnswerEvaluation
    next_question_available: bool
    transcription: str | None = None
    media: MediaInfo | None = None


class ReportItem(BaseModel):
    question: str
    answer: str
    answer_id: int
    score_overall: int
    score_clarity: int
    score_confidence: int
    filler_word_count: int
    strengths: List[str]
    improvements: List[str]
    feedback: str
    media: MediaInfo | None = None

    # Coding and Technical evaluations
    submitted_code: str | None = None
    code_time_complexity: str | None = None
    code_space_complexity: str | None = None
    code_cleanliness_score: int | None = None
    code_error_resilience: int | None = None
    code_syntax_passes: bool | None = None
    
    # Technical / Non-Technical sub-scores
    technical_fluency: int = 50
    non_technical_communication: int = 50

    # Behavioral KPIs
    growth_mindset: int = 50
    ownership: int = 50
    collaborative_empathy: int = 50
    stress_resilience: int = 50
    professional_integrity: int = 50


class MediaAnalyticsRequest(BaseModel):
    playback_event: str = "playback"


class ContextFactorsRequest(BaseModel):
    family_pressure: str = "Medium"
    financial_dependency: str = "Yes"
    confidence_baseline: int = 50
    stress_baseline: int = 50
    resilience_rating: int = 50
    income_tier: str = "Middle Class"
    city_tier: str = "Tier 2"
    college_tier: str = "Tier 2"


class StudentSkillRequest(BaseModel):
    name: str
    category: str  # Technical, Non-Technical
    proficiency: str = "Intermediate"


class StudentSkillResponse(BaseModel):
    id: int
    name: str
    category: str
    proficiency: str
    verification_status: str


class StudentCertificationRequest(BaseModel):
    title: str
    issuer: str
    issue_date: str | None = None
    credential_id: str | None = None
    file_url: str | None = None


class StudentCertificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    issuer: str
    issue_date: str | None = None
    credential_id: str | None = None
    verification_status: str
    file_url: str | None = None
    reviewer_notes: str | None = None


class StudentLinkRequest(BaseModel):
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    leetcode_url: str | None = None


class StudentLinkResponse(BaseModel):
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    leetcode_url: str | None = None


class HitlReviewQueueCreate(BaseModel):
    task_type: str
    flag_reason: str


class HitlQueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    learner_id: int
    learner_name: str | None = None
    task_type: str
    status: str
    certificate_title: str | None = None
    issuer: str | None = None
    credential_id: str | None = None
    file_url: str | None = None
    flag_reason: str | None = None
    reviewer_notes: str | None = None


class CareerShiftRequest(BaseModel):
    target_role: str
    shift_reason: str


class CareerShiftResponse(BaseModel):
    transferable_skills: List[str]
    gaps: List[str]
    remediation_delta: List[str]
    reason: str


class ReadinessDiagnosisRequest(BaseModel):
    user_name: str | None = None
    target_role: str = Field(default="", max_length=120)
    experience_level: str = Field(default="", max_length=60)
    stream: str = Field(default="Engineering and Technology", max_length=120)
    dream_role: str = Field(default="", max_length=240)
    dream_reason: str = Field(default="", max_length=800)
    impact: str = Field(default="", max_length=800)
    lifestyle: str = Field(default="", max_length=800)
    strengths: str = Field(default="", max_length=800)
    fears: str = Field(default="", max_length=800)
    identity_goal: str = Field(default="", max_length=800)
    reflection: str = Field(default="", max_length=1500)
    dimension_scores: Dict[str, int] = Field(default_factory=dict)
    portfolio_evidence: List[str] = Field(default_factory=list)
    context_factors: Dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    session_id: int
    user_name: str
    target_role: str
    experience_level: str
    difficulty: str | None = None
    overall_score: int
    clarity_score: int
    confidence_score: int
    total_filler_words: int
    status: str
    strengths_summary: List[str]
    improvement_summary: List[str]
    recommended_next_steps: List[str]
    items: List[ReportItem]


class LmsLectureResponse(BaseModel):
    id: int
    module_id: int
    title: str
    content_type: str
    content: str
    mantras: str | None = None


class LmsModuleResponse(BaseModel):
    id: int
    title: str
    order_no: int
    lectures: List[LmsLectureResponse] = []


class LmsCourseResponse(BaseModel):
    id: int
    title: str
    description: str
    instructor: str
    stream: str
    duration: str
    difficulty: str
    modules: List[LmsModuleResponse] = []


class LmsEnrollRequest(BaseModel):
    course_id: int


class LmsProgressResponse(BaseModel):
    course_id: int
    progress_percent: int
    completed_lectures: List[int]


class LmsPostRequest(BaseModel):
    text: str


class LmsCollaborationPostResponse(BaseModel):
    id: int
    user_name: str
    text: str
    created_at: Any

class JobSearchResponse(BaseModel):
    id: int
    title: str
    organization: str
    type: str
    required_skills: List[str]
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    url: str
    match_score: int


class MentorshipBookRequest(BaseModel):
    mentor_name: str
    date_str: str
    time_str: str
    meeting_type: str | None = "Google Meet"
    custom_url: str | None = None


class MentorshipUpdateRequest(BaseModel):
    mentor_name: str
    date_str: str
    time_str: str
    meeting_type: str | None = "Google Meet"
    custom_url: str | None = None


class MentorshipSessionResponse(BaseModel):
    id: int
    mentor_name: str
    date_str: str
    time_str: str
    meet_url: str
    meeting_type: str | None = None
    meeting_id: str | None = None
    notes: str
    feedback: str
    status: str


class SecurityPolicyLogResponse(BaseModel):
    id: int
    ip_address: str
    category: str
    action_attempt: str
    status: str
    created_at: Any


class FeedbackLoopResponse(BaseModel):
    id: int
    trigger_event: str
    action_taken: str
    status: str
    created_at: Any


class PlatformMoatResponse(BaseModel):
    metric_key: str
    metric_val: str


class ReadinessProceedingResponse(BaseModel):
    id: int
    flow_stage: str
    description: str
    metrics_snapshot: Dict[str, Any]
    strategic_action: str
    created_at: Any


class MentorRosterItemResponse(BaseModel):
    learner_id: int
    learner_name: str
    stream: str | None = None
    target_role: str | None = None
    cari: int | None = None
    readiness_level: str | None = None
    top_gap: str | None = None


class MentorDiagnosticSnapshotResponse(BaseModel):
    learner_id: int
    learner_name: str
    stream: str | None = None
    target_roles: str | None = None
    cari: int | None = None
    readiness_level: str | None = None
    scorecard: Dict[str, Any] | None = None
    gaps: List[Dict[str, Any]] = []
    skills: List[Dict[str, Any]] = []


class CompetencyGapResponse(BaseModel):
    name: str
    value: int
    status: str


class InstitutionLearnerResponse(BaseModel):
    learner_id: int
    learner_name: str
    target_role: str | None = None
    readiness_score: int | None = None
    readiness_status: str | None = None


class InstitutionAnalyticsResponse(BaseModel):
    employment_readiness_rate: str
    cohort_skill_convergence: str
    skilling_partner_roi: str
    competency_gaps: List[CompetencyGapResponse]
    cohort_size: int
    learners: List[InstitutionLearnerResponse]

class EmployerMatchResponse(BaseModel):
    learner_id: int
    candidate_name: str
    target_role: str
    stream: str
    armc_score: int
    matched_skills: List[str]

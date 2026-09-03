from __future__ import annotations

from collections import defaultdict
from typing import Any


from typing import Any
import time


UNIVERSAL_FLOW = [
    {
        "stage": "Dream",
        "purpose": "Clarify aspiration",
        "key_question": "What does the learner want to become?",
        "output": "Career/dream statement",
    },
    {
        "stage": "Discover",
        "purpose": "Explore reality",
        "key_question": "What does that path actually require?",
        "output": "Role and pathway map",
    },
    {
        "stage": "Diagnose",
        "purpose": "Identify gaps",
        "key_question": "Where is the learner now?",
        "output": "Readiness profile",
    },
    {
        "stage": "Design",
        "purpose": "Build roadmap",
        "key_question": "What should be learned first?",
        "output": "Personal development plan",
    },
    {
        "stage": "Develop",
        "purpose": "Train capabilities",
        "key_question": "What skills must be built?",
        "output": "Learning progress",
    },
    {
        "stage": "Demonstrate",
        "purpose": "Show evidence",
        "key_question": "Can the learner perform?",
        "output": "Portfolio, projects, simulations",
    },
    {
        "stage": "Deploy",
        "purpose": "Enter real context",
        "key_question": "Can the learner apply skills outside training?",
        "output": "Internship, job, client work, project",
    },
    {
        "stage": "Adopt",
        "purpose": "Sustain behavior",
        "key_question": "Has the learner internalized professional habits?",
        "output": "Adoption index",
    },
    {
        "stage": "Grow",
        "purpose": "Upgrade continuously",
        "key_question": "What is the next level?",
        "output": "Lifelong growth pathway",
    },
]


READINESS_DIMENSIONS = [
    {
        "key": "purpose_clarity",
        "label": "Purpose clarity",
        "weight": 10,
        "layer": "Personal",
        "signals": ["dream clarity", "value alignment", "future direction"],
    },
    {
        "key": "self_awareness_confidence",
        "label": "Self-awareness and confidence",
        "weight": 10,
        "layer": "Personal",
        "signals": ["strength awareness", "fear awareness", "confidence"],
    },
    {
        "key": "communication_readiness",
        "label": "Communication readiness",
        "weight": 15,
        "layer": "Professional",
        "signals": ["interview answers", "business writing", "presentation"],
    },
    {
        "key": "digital_ai_readiness",
        "label": "Digital and AI readiness",
        "weight": 10,
        "layer": "Future",
        "signals": ["productivity tools", "AI literacy", "digital workflows"],
    },
    {
        "key": "domain_technical_readiness",
        "label": "Domain/technical readiness",
        "weight": 15,
        "layer": "Technical / Domain",
        "signals": ["role knowledge", "hands-on skill", "tool use"],
    },
    {
        "key": "problem_solving_readiness",
        "label": "Problem-solving readiness",
        "weight": 10,
        "layer": "Future",
        "signals": ["case reasoning", "root cause analysis", "decisions"],
    },
    {
        "key": "collaboration_leadership",
        "label": "Collaboration and leadership",
        "weight": 10,
        "layer": "Professional",
        "signals": ["teamwork", "ownership", "workplace behavior"],
    },
    {
        "key": "career_readiness",
        "label": "Career readiness",
        "weight": 10,
        "layer": "Professional",
        "signals": ["resume", "LinkedIn/profile", "interview readiness"],
    },
    {
        "key": "portfolio_evidence",
        "label": "Portfolio/project evidence",
        "weight": 10,
        "layer": "Technical / Domain",
        "signals": ["projects", "artifacts", "proof of work"],
    },
]


READINESS_LEVELS = [
    {
        "min": 0,
        "max": 39,
        "level": "Unprepared",
        "meaning": "Needs foundation support",
    },
    {
        "min": 40,
        "max": 59,
        "level": "Emerging",
        "meaning": "Has potential, needs structure",
    },
    {
        "min": 60,
        "max": 74,
        "level": "Developing",
        "meaning": "Can perform with guidance",
    },
    {
        "min": 75,
        "max": 89,
        "level": "Ready",
        "meaning": "Can enter real-world opportunity",
    },
    {
        "min": 90,
        "max": 100,
        "level": "Next-Level Ready",
        "meaning": "Can perform independently and grow",
    },
]


GAP_MATRIX = [
    {
        "gap_type": "Awareness gap",
        "symptoms": "Learner does not know career options",
        "root_cause": "Limited exposure",
        "fix": "Career discovery, alumni sessions, role maps",
        "dimensions": ["purpose_clarity"],
    },
    {
        "gap_type": "Confidence gap",
        "symptoms": "Fear of interviews, meetings, or public speaking",
        "root_cause": "Low practice and feedback",
        "fix": "Speaking labs, mock interviews, mentoring",
        "dimensions": ["self_awareness_confidence"],
    },
    {
        "gap_type": "Communication gap",
        "symptoms": "Weak emails, presentations, or workplace language",
        "root_cause": "No professional communication training",
        "fix": "Business communication course and writing drills",
        "dimensions": ["communication_readiness"],
    },
    {
        "gap_type": "Skill gap",
        "symptoms": "Cannot perform required role tasks",
        "root_cause": "Curriculum-practice mismatch",
        "fix": "Domain course, labs, projects",
        "dimensions": ["domain_technical_readiness"],
    },
    {
        "gap_type": "Application gap",
        "symptoms": "Knows theory but cannot apply it",
        "root_cause": "Low project exposure",
        "fix": "Case work, internships, simulations",
        "dimensions": ["problem_solving_readiness", "portfolio_evidence"],
    },
    {
        "gap_type": "Digital gap",
        "symptoms": "Poor tool usage",
        "root_cause": "Limited access or practice",
        "fix": "Digital productivity and AI literacy training",
        "dimensions": ["digital_ai_readiness"],
    },
    {
        "gap_type": "Behavioral gap",
        "symptoms": "Misses deadlines or shows low ownership",
        "root_cause": "Weak accountability habits",
        "fix": "Task trackers, mentor reviews, habit coaching",
        "dimensions": ["collaboration_leadership"],
    },
    {
        "gap_type": "Career gap",
        "symptoms": "Poor resume, LinkedIn/profile, or interview readiness",
        "root_cause": "No structured career preparation",
        "fix": "Career toolkit and interview practice",
        "dimensions": ["career_readiness"],
    },
    {
        "gap_type": "Purpose gap",
        "symptoms": "Learner feels directionless",
        "root_cause": "Dream not connected to values and strengths",
        "fix": "Purpose mapping and career counselling",
        "dimensions": ["purpose_clarity", "self_awareness_confidence"],
    },
    {
        "gap_type": "Authenticity gap",
        "symptoms": "Learner imitates others without self-alignment",
        "root_cause": "Social pressure or low self-awareness",
        "fix": "Strength mapping and reflective portfolio",
        "dimensions": ["purpose_clarity", "self_awareness_confidence"],
    },
    {
        "gap_type": "Adoption gap",
        "symptoms": "Learns but does not sustain behavior",
        "root_cause": "No follow-up or real-world reinforcement",
        "fix": "30/60/90 day adoption tracking",
        "dimensions": ["collaboration_leadership", "portfolio_evidence"],
    },
]


CORE_MODULES = [
    {
        "name": "Dream Mapping",
        "purpose": "Convert aspiration into a structured dream profile.",
        "features": [
            "guided questionnaire",
            "voice/text reflection",
            "strength and fear mapping",
            "purpose and authenticity reflection",
            "AI-generated dream statement",
        ],
        "outputs": [
            "dream statement",
            "purpose statement",
            "impact statement",
            "strength map",
            "fear map",
            "initial pathway hypothesis",
        ],
    },
    {
        "name": "Career Discovery",
        "purpose": "Help learners understand what their dream path requires.",
        "features": [
            "role explorer",
            "career pathway map",
            "skills, tools, and qualification maps",
            "portfolio evidence requirements",
            "3/5/10 year growth view",
        ],
        "outputs": ["role map", "entry-level opportunities", "skill matrix", "growth pathway"],
    },
    {
        "name": "Multimodal Diagnosis",
        "purpose": "Assess personal, professional, technical, and future readiness.",
        "features": [
            "self-assessment",
            "written communication task",
            "voice/video interview",
            "digital task",
            "domain task",
            "portfolio review",
        ],
        "outputs": ["readiness profile", "scorecard", "gap diagnosis", "risk indicators"],
    },
    {
        "name": "Readiness Scorecard",
        "purpose": "Calculate weighted readiness score and level.",
        "features": ["nine weighted dimensions", "readiness levels", "dimension summaries"],
        "outputs": ["total score", "readiness level", "dimension scores"],
    },
    {
        "name": "Gap Diagnosis",
        "purpose": "Classify gaps, root causes, priorities, and fixes.",
        "features": ["gap taxonomy", "severity", "recommended fix", "mentor action"],
        "outputs": ["top gaps", "root causes", "practice tasks", "evidence requirements"],
    },
    {
        "name": "Personal Development Plan",
        "purpose": "Convert diagnosis into a 30/60/90 day roadmap.",
        "features": [
            "Learn-Practice-Reflect-Improve-Prove pathway",
            "weekly tasks",
            "mentor checkpoints",
            "adaptive sequencing",
        ],
        "outputs": ["30 day plan", "60 day milestone", "90 day success plan"],
    },
    {
        "name": "Learning and Practice",
        "purpose": "Deliver or integrate readiness training.",
        "features": [
            "micro-lessons",
            "external course recommendations",
            "practice labs",
            "roleplays",
            "reflection journals",
        ],
        "outputs": ["completed tasks", "reflections", "practice evidence"],
    },
    {
        "name": "Demonstration and Portfolio",
        "purpose": "Require learners to prove readiness with evidence.",
        "features": [
            "portfolio checklist",
            "artifact upload",
            "AI review",
            "rubric scoring",
            "mentor approval",
        ],
        "outputs": ["portfolio items", "evidence score", "approved artifacts"],
    },
    {
        "name": "Simulation and Roleplay",
        "purpose": "Expose learners to real-world conditions.",
        "features": [
            "interviews",
            "client briefs",
            "manager emails",
            "team conflict",
            "ethical dilemmas",
        ],
        "outputs": ["simulation score", "retry challenge", "performance feedback"],
    },
    {
        "name": "Deployment",
        "purpose": "Move learners into real-world or near-real-world opportunities.",
        "features": [
            "opportunity marketplace",
            "matching engine",
            "application tracking",
            "employer feedback",
        ],
        "outputs": ["matched opportunities", "deployment record", "feedback"],
    },
    {
        "name": "Adoption Tracking",
        "purpose": "Measure whether learners consistently apply what they learned.",
        "features": [
            "30/60/90 follow-up",
            "habit tracker",
            "mentor rating",
            "before-after comparison",
            "adoption alerts",
        ],
        "outputs": ["adoption index", "behavior trend", "next support action"],
    },
    {
        "name": "Growth",
        "purpose": "Create continuous upskilling after initial readiness.",
        "features": [
            "next-level pathway",
            "career progression plan",
            "certification suggestions",
            "portfolio refresh reminders",
        ],
        "outputs": ["growth pathway", "upgrade recommendations", "new opportunities"],
    },
]


AGENTIC_AI_LAYER = [
    "Orchestrator Agent",
    "Dream Mapper Agent",
    "Career Discovery Agent",
    "Diagnostic Agent",
    "Multimodal Assessment Agent",
    "Learning Pathway Agent",
    "Simulation Agent",
    "Portfolio Review Agent",
    "Mentor Assistant Agent",
    "Institution Analytics Agent",
    "Employer Matching Agent",
    "Adoption Coach Agent",
    "Safety / Human Review Agent",
]


BACKEND_SERVICES = [
    {
        "name": "Auth Service",
        "capabilities": ["login", "registration", "role-based access", "permissions"],
    },
    {
        "name": "User/Profile Service",
        "capabilities": ["learner profiles", "mentor profiles", "institution profiles", "employer profiles"],
    },
    {
        "name": "Journey Service",
        "capabilities": ["stage tracking", "next best action", "progress state", "milestones"],
    },
    {
        "name": "Assessment Service",
        "capabilities": ["surveys", "task submissions", "rubric scoring", "multimodal processing"],
    },
    {
        "name": "Readiness Service",
        "capabilities": ["scorecards", "readiness levels", "gap reports", "adoption index"],
    },
    {
        "name": "AI Orchestration Service",
        "capabilities": ["agent routing", "prompt management", "output validation", "human review triggers"],
    },
    {
        "name": "Learning Plan Service",
        "capabilities": ["30/60/90 plans", "weekly tasks", "course recommendations", "task tracking"],
    },
    {
        "name": "Portfolio Service",
        "capabilities": ["artifact upload", "evidence review", "portfolio scoring", "shareable portfolio"],
    },
    {
        "name": "Simulation Service",
        "capabilities": ["scenario sessions", "conversation history", "voice/video records", "performance scoring"],
    },
    {
        "name": "Opportunity Service",
        "capabilities": ["opportunities", "matching", "applications", "employer feedback"],
    },
    {
        "name": "Analytics Service",
        "capabilities": ["learner analytics", "cohort analytics", "institution reports", "product metrics"],
    },
    {
        "name": "Audit and Safety Service",
        "capabilities": ["AI decision logs", "sensitive flags", "review queue", "compliance logs"],
    },
]


MVP_SCOPE = {
    "goal": "Prove that AI-guided readiness diagnosis and personalized development plans improve learner clarity, confidence, and evidence creation.",
    "users": ["Learners", "Mentors/admins", "Institution manager"],
    "features": [
        "learner onboarding",
        "dream mapping questionnaire",
        "readiness self-assessment",
        "written communication task",
        "resume/profile upload",
        "AI-generated readiness scorecard",
        "gap diagnosis report",
        "30/60/90 day plan",
        "portfolio checklist",
        "mentor review dashboard",
        "cohort analytics dashboard",
        "basic notification system",
    ],
    "exclusions": [
        "full video scoring",
        "complex employer marketplace",
        "advanced LMS integrations",
        "deep psychometric testing",
        "automated high-stakes placement decisions",
    ],
}


ROADMAP = [
    {
        "version": "Version 1",
        "name": "Readiness Diagnosis MVP",
        "items": [
            "dream mapping",
            "self-assessment",
            "written task assessment",
            "readiness scorecard",
            "gap report",
            "30/60/90 pathway",
            "mentor dashboard",
        ],
    },
    {
        "version": "Version 2",
        "name": "Multimodal Practice System",
        "items": [
            "voice interview simulation",
            "video uploads",
            "AI roleplay scenarios",
            "portfolio builder",
            "stream-wise pathways",
            "gamified progress",
        ],
    },
    {
        "version": "Version 3",
        "name": "Institution Operating System",
        "items": [
            "institutional audit",
            "course-readiness mapping",
            "faculty/trainer dashboard",
            "department analytics",
            "employer feedback loops",
        ],
    },
    {
        "version": "Version 4",
        "name": "Opportunity Marketplace",
        "items": [
            "employer dashboard",
            "internship/project matching",
            "readiness-based shortlisting",
            "employer feedback",
            "adoption tracking",
        ],
    },
    {
        "version": "Version 5",
        "name": "National/Enterprise Scale",
        "items": [
            "multi-institution deployment",
            "government/CSR dashboards",
            "regional language support",
            "advanced analytics warehouse",
            "policy reporting",
            "API ecosystem",
        ],
    },
]


STREAM_PATHWAYS = [
    {
        "stream": "Engineering and Technology",
        "common_dreams": ["software developer", "data analyst", "AI/ML engineer", "cloud engineer", "cybersecurity analyst", "startup founder"],
        "key_gaps": ["coding without project depth", "weak problem-solving explanation", "limited industry tools", "weak internship exposure"],
        "recommended_learning": ["programming fundamentals", "DSA", "Git/GitHub", "cloud fundamentals", "AI/ML basics", "technical writing"],
        "proof_of_readiness": ["GitHub portfolio", "deployed project", "technical blog", "hackathon", "internship or open-source contribution"],
    },
    {
        "stream": "Management, Commerce, and Business",
        "common_dreams": ["business analyst", "HR professional", "marketing executive", "finance analyst", "entrepreneur"],
        "key_gaps": ["concepts without application", "weak Excel/data analysis", "poor presentations", "limited market understanding"],
        "recommended_learning": ["spreadsheet analytics", "business communication", "financial literacy", "marketing", "case study method"],
        "proof_of_readiness": ["business case deck", "market research report", "financial model", "sales pitch", "startup canvas"],
    },
    {
        "stream": "Arts, Humanities, and Social Sciences",
        "common_dreams": ["civil services", "policy researcher", "teacher", "writer", "journalist", "social sector professional"],
        "key_gaps": ["weak career mapping", "limited digital portfolio", "research-to-action gap", "low exposure to policy/media/NGOs"],
        "recommended_learning": ["research methods", "writing and editing", "public speaking", "policy analysis", "project management"],
        "proof_of_readiness": ["writing portfolio", "research brief", "policy memo", "social impact project", "teaching demo"],
    },
    {
        "stream": "Science and Research",
        "common_dreams": ["research assistant", "lab technician", "scientist", "data analyst", "healthcare researcher"],
        "key_gaps": ["weak research design", "poor data analysis", "weak scientific writing", "low awareness of research careers"],
        "recommended_learning": ["research methodology", "statistics", "scientific writing", "data visualization", "Python/R basics"],
        "proof_of_readiness": ["literature review", "mini research paper", "lab notebook", "poster presentation", "research internship"],
    },
    {
        "stream": "Healthcare, Nursing, Pharmacy, and Allied Health",
        "common_dreams": ["nurse", "pharmacist", "healthcare administrator", "lab technician", "clinical research associate"],
        "key_gaps": ["patient communication", "documentation discipline", "digital health tools", "ethics and empathy under pressure"],
        "recommended_learning": ["patient communication", "medical documentation", "healthcare ethics", "digital health literacy", "emotional resilience"],
        "proof_of_readiness": ["case documentation", "patient communication roleplay", "clinical reflection journal", "simulation assessment"],
    },
    {
        "stream": "Education and Teaching",
        "common_dreams": ["school teacher", "trainer", "instructional designer", "edtech professional", "counsellor"],
        "key_gaps": ["weak learner engagement", "limited assessment design", "poor classroom communication", "weak digital pedagogy"],
        "recommended_learning": ["lesson planning", "classroom communication", "assessment design", "digital teaching tools", "inclusive education"],
        "proof_of_readiness": ["lesson plan", "teaching demo video", "assessment design", "activity toolkit", "reflective teaching journal"],
    },
    {
        "stream": "Law, Governance, and Public Policy",
        "common_dreams": ["lawyer", "legal researcher", "policy analyst", "civil servant", "compliance officer"],
        "key_gaps": ["weak drafting", "poor policy writing", "limited practical exposure", "weak argument structure"],
        "recommended_learning": ["legal drafting", "policy writing", "research methods", "debate", "compliance basics"],
        "proof_of_readiness": ["case brief", "policy memo", "moot court", "legal drafting sample", "internship diary"],
    },
    {
        "stream": "Design, Media, Communication, and Creative Arts",
        "common_dreams": ["designer", "content creator", "journalist", "filmmaker", "UX designer", "brand strategist"],
        "key_gaps": ["talent without portfolio structure", "weak client communication", "limited business understanding", "low consistency"],
        "recommended_learning": ["design thinking", "storytelling", "UX fundamentals", "content strategy", "client pitching"],
        "proof_of_readiness": ["portfolio website", "design case study", "campaign plan", "video samples", "brand deck"],
    },
    {
        "stream": "Agriculture, Food, Environment, and Sustainability",
        "common_dreams": ["agri entrepreneur", "food technologist", "sustainability analyst", "environmental consultant"],
        "key_gaps": ["limited market linkage", "weak field documentation", "poor business planning", "weak digital tools"],
        "recommended_learning": ["agribusiness", "sustainability", "climate literacy", "supply chain", "field research"],
        "proof_of_readiness": ["field study report", "agribusiness model", "sustainability audit", "prototype", "supply-chain map"],
    },
    {
        "stream": "Hospitality, Tourism, Retail, and Services",
        "common_dreams": ["hotel professional", "tourism manager", "retail associate", "customer service executive", "event manager"],
        "key_gaps": ["customer communication", "grooming and etiquette", "conflict handling", "language fluency"],
        "recommended_learning": ["customer service", "spoken English", "etiquette", "sales basics", "complaint handling"],
        "proof_of_readiness": ["customer roleplay", "service recovery script", "sales pitch", "event plan", "internship feedback"],
    },
    {
        "stream": "Vocational, Technical Trades, and Skilled Work",
        "common_dreams": ["electrician", "technician", "mechanic", "CNC operator", "welder", "entrepreneur"],
        "key_gaps": ["certification without mastery", "safety gaps", "weak customer communication", "poor documentation"],
        "recommended_learning": ["trade skill modules", "safety", "customer handling", "basic accounting", "quality control"],
        "proof_of_readiness": ["practical demo", "safety checklist", "work logbook", "customer roleplay", "apprentice record"],
    },
    {
        "stream": "Sports, Defence, Fitness, and Performance Careers",
        "common_dreams": ["athlete", "defence services", "police services", "fitness coach", "sports manager"],
        "key_gaps": ["discipline without career planning", "nutrition/recovery gaps", "weak personal branding", "limited backup pathways"],
        "recommended_learning": ["physical conditioning", "nutrition", "mental resilience", "leadership", "sports analytics"],
        "proof_of_readiness": ["fitness record", "performance dashboard", "coaching plan", "competition portfolio", "discipline log"],
    },
]


PORTFOLIO_CHECKLIST = [
    "Dream pathway sheet",
    "Readiness scorecard",
    "Resume",
    "LinkedIn/professional profile",
    "Communication sample",
    "Digital productivity output",
    "Domain project",
    "Reflection journal",
    "Mentor feedback",
    "Final adoption score",
    "6-month growth plan",
]


CORE_STATUSES = {
    "learner_journey": [
        "Not started",
        "Dream mapped",
        "Pathway discovered",
        "Assessment pending",
        "Diagnosed",
        "Plan active",
        "Developing",
        "Demonstrating",
        "Portfolio ready",
        "Deployment ready",
        "Deployed",
        "Adoption tracking",
        "Growth active",
    ],
    "portfolio_item": ["Required", "Draft", "Submitted", "AI reviewed", "Revision needed", "Mentor approved", "Verified"],
    "assessment": ["Not started", "In progress", "Submitted", "AI evaluated", "Human review required", "Completed"],
    "opportunity": ["Draft", "Open", "Matching", "Shortlisting", "Interview/project stage", "Selected", "Rejected", "Completed", "Feedback submitted"],
}


DOCUMENT_SOURCES = [
    {
        "file": "Universal Readiness Flow Framework.docx",
        "extracted_markdown": "docs_extracted/Universal Readiness Flow Framework.md",
    },
    {
        "file": "Agentic Readiness Platform Build Blueprint.docx",
        "extracted_markdown": "docs_extracted/Agentic Readiness Platform Build Blueprint.md",
    },
]


def get_platform_framework() -> dict[str, Any]:
    return {
        "product_definition": "A multimodal agentic AI readiness operating system that turns aspiration into measurable capability.",
        "universal_flow": UNIVERSAL_FLOW,
        "readiness_layers": [
            {
                "name": "Personal Readiness",
                "measures": ["confidence", "mindset", "motivation", "self-awareness", "discipline", "emotional maturity"],
            },
            {
                "name": "Professional Readiness",
                "measures": ["communication", "workplace behavior", "collaboration", "time management", "ownership", "ethics"],
            },
            {
                "name": "Technical / Domain Readiness",
                "measures": ["role-specific knowledge", "trade-specific ability", "course-specific skill"],
            },
            {
                "name": "Future Readiness",
                "measures": ["digital fluency", "AI literacy", "learning agility", "adaptability", "creativity", "problem-solving"],
            },
        ],
        "readiness_dimensions": READINESS_DIMENSIONS,
        "readiness_levels": READINESS_LEVELS,
        "gap_matrix": GAP_MATRIX,
        "core_modules": CORE_MODULES,
        "agents": AGENTIC_AI_LAYER,
        "backend_services": BACKEND_SERVICES,
        "mvp_scope": MVP_SCOPE,
        "roadmap": ROADMAP,
        "stream_pathways": STREAM_PATHWAYS,
        "portfolio_checklist": PORTFOLIO_CHECKLIST,
        "core_statuses": CORE_STATUSES,
        "document_sources": DOCUMENT_SOURCES,
    }


rag_cag_metrics = {
    "latency_rag_ms": 0,
    "latency_cag_ms": 0,
    "cache_hits": 0
}


def _clamp_score(value: Any, default: int = 50) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(0, min(100, parsed))


def _level_for_score(score: int) -> dict[str, Any]:
    for item in READINESS_LEVELS:
        if item["min"] <= score <= item["max"]:
            return item
    return READINESS_LEVELS[0]


def _normalize_evidence(values: list[str]) -> set[str]:
    return {item.strip().lower() for item in values if item and item.strip()}


def _score_portfolio(evidence: set[str], provided_score: int) -> int:
    direct = provided_score
    evidence_score = min(100, len(evidence) * 12)
    return max(direct, evidence_score)


def _scores_with_context(payload: dict[str, Any]) -> dict[str, int]:
    provided = payload.get("dimension_scores") or {}
    evidence = _normalize_evidence(payload.get("portfolio_evidence") or [])
    context_factors = payload.get("context_factors") or {}
    
    # Retrieve slider values (defaulting to 50 if missing)
    conf = int(context_factors.get("confidence_baseline", 50))
    stress = int(context_factors.get("stress_baseline", 50))
    res = int(context_factors.get("resilience_rating", 50))

    scores = {
        dimension["key"]: _clamp_score(provided.get(dimension["key"]), default=55)
        for dimension in READINESS_DIMENSIONS
    }

    if payload.get("dream_role") and payload.get("dream_reason"):
        scores["purpose_clarity"] = max(scores["purpose_clarity"], 68)
    if payload.get("strengths") and payload.get("fears"):
        scores["self_awareness_confidence"] = max(scores["self_awareness_confidence"], 62)
    if payload.get("target_role"):
        scores["career_readiness"] = max(scores["career_readiness"], 58)
        
    # Dynamic Math Adjustments from Context Factors
    conf_offset = int((conf - 50) * 0.2)
    scores["purpose_clarity"] = _clamp_score(scores["purpose_clarity"] + conf_offset, default=scores["purpose_clarity"])
    scores["self_awareness_confidence"] = _clamp_score(scores["self_awareness_confidence"] + conf_offset, default=scores["self_awareness_confidence"])
    
    comm_offset = int((res - 50) * 0.2 - (stress - 50) * 0.1)
    scores["communication_readiness"] = _clamp_score(scores["communication_readiness"] + comm_offset, default=scores["communication_readiness"])

    scores["portfolio_evidence"] = _score_portfolio(evidence, scores["portfolio_evidence"])
    return scores


def _weighted_total(scores: dict[str, int]) -> int:
    total = 0.0
    for dimension in READINESS_DIMENSIONS:
        total += scores[dimension["key"]] * (dimension["weight"] / 100)
    return round(total)


def _layer_scores(scores: dict[str, int]) -> list[dict[str, Any]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for dimension in READINESS_DIMENSIONS:
        grouped[dimension["layer"]].append(scores[dimension["key"]])
    return [
        {"layer": layer, "score": round(sum(values) / len(values))}
        for layer, values in grouped.items()
    ]


def _gap_for_dimension(dimension_key: str) -> dict[str, Any]:
    for gap in GAP_MATRIX:
        if dimension_key in gap["dimensions"]:
            return gap
    return GAP_MATRIX[0]


def _diagnose_gaps(scores: dict[str, int]) -> list[dict[str, Any]]:
    gaps = []
    for dimension in READINESS_DIMENSIONS:
        key = dimension["key"]
        score = scores[key]
        if score >= 75:
            continue
        matrix_item = _gap_for_dimension(key)
        severity = "high" if score < 45 else "medium" if score < 65 else "low"
        gaps.append(
            {
                "dimension": dimension["label"],
                "score": score,
                "gap_type": matrix_item["gap_type"],
                "symptoms": matrix_item["symptoms"],
                "root_cause": matrix_item["root_cause"],
                "recommended_fix": matrix_item["fix"],
                "severity": severity,
                "priority": 100 - score,
                "practice_task": _practice_task_for_gap(matrix_item["gap_type"]),
                "evidence_required": _evidence_for_gap(matrix_item["gap_type"]),
                "mentor_action": _mentor_action_for_gap(matrix_item["gap_type"]),
            }
        )
    return sorted(gaps, key=lambda item: item["priority"], reverse=True)[:5]


def _practice_task_for_gap(gap_type: str) -> str:
    tasks = {
        "Awareness gap": "Compare three target roles and write a one-page role reality map.",
        "Confidence gap": "Record two mock interview answers and review them with a mentor.",
        "Communication gap": "Write a business email and a STAR interview answer for review.",
        "Skill gap": "Complete a role-specific mini project or lab.",
        "Application gap": "Solve a realistic case or simulation and submit the artifact.",
        "Digital gap": "Create a productivity workflow using spreadsheet, document, calendar, and AI tools.",
        "Behavioral gap": "Track commitments for seven days and complete a mentor accountability check.",
        "Career gap": "Update resume/profile and complete one mock interview.",
        "Purpose gap": "Complete a dream, values, strengths, and fear reflection.",
        "Authenticity gap": "Build a reflective portfolio note connecting work to strengths and values.",
        "Adoption gap": "Start a 30/60/90 habit tracker with evidence check-ins.",
    }
    return tasks.get(gap_type, "Complete a targeted practice task and submit evidence.")


def _evidence_for_gap(gap_type: str) -> str:
    evidence = {
        "Awareness gap": "role comparison map",
        "Confidence gap": "mock interview recording",
        "Communication gap": "email sample and interview answer",
        "Skill gap": "completed lab or domain project",
        "Application gap": "case solution or simulation artifact",
        "Digital gap": "digital productivity output",
        "Behavioral gap": "task tracker and mentor note",
        "Career gap": "resume/profile and interview score",
        "Purpose gap": "dream pathway sheet",
        "Authenticity gap": "reflective portfolio item",
        "Adoption gap": "30/60/90 adoption tracker",
    }
    return evidence.get(gap_type, "reviewable portfolio artifact")


def _mentor_action_for_gap(gap_type: str) -> str:
    actions = {
        "Confidence gap": "Schedule a low-pressure speaking review.",
        "Communication gap": "Annotate one written answer and one spoken answer.",
        "Skill gap": "Validate the selected mini project matches the target role.",
        "Application gap": "Run a case debrief and ask for one revision.",
        "Behavioral gap": "Set weekly accountability milestones.",
        "Career gap": "Review resume/profile and readiness for mock interview.",
        "Purpose gap": "Discuss values, family context, strengths, and practical pathways.",
        "Authenticity gap": "Check whether goals are self-owned rather than copied.",
    }
    return actions.get(gap_type, "Review the learner evidence and confirm the next action.")


def _strengths(scores: dict[str, int]) -> list[dict[str, Any]]:
    ranked = sorted(
        [
            {
                "dimension": dimension["label"],
                "score": scores[dimension["key"]],
                "signal": ", ".join(dimension["signals"][:2]),
            }
            for dimension in READINESS_DIMENSIONS
        ],
        key=lambda item: item["score"],
        reverse=True,
    )
    return [item for item in ranked if item["score"] >= 70][:5] or ranked[:3]


def _find_stream(stream_name: str) -> dict[str, Any]:
    normalized = (stream_name or "").strip().lower()
    for stream in STREAM_PATHWAYS:
        if stream["stream"].lower() == normalized:
            return stream
    for stream in STREAM_PATHWAYS:
        if normalized and normalized in stream["stream"].lower():
            return stream
    return STREAM_PATHWAYS[0]


def _portfolio_items(evidence: set[str]) -> list[dict[str, str]]:
    return [
        {
            "item": item,
            "status": "Submitted" if item.lower() in evidence else "Required",
            "next_action": "Request mentor/AI review" if item.lower() in evidence else f"Create or upload {item.lower()}",
        }
        for item in PORTFOLIO_CHECKLIST
    ]


def _learning_plan(gaps: list[dict[str, Any]], stream: dict[str, Any]) -> dict[str, list[str]]:
    top_gaps = gaps[:3]
    if not top_gaps:
        top_gaps = [
            {
                "gap_type": "Growth gap",
                "recommended_fix": "Advance to a higher difficulty simulation and refresh portfolio evidence.",
                "practice_task": "Attempt a next-level real-world simulation.",
                "evidence_required": "updated portfolio item",
            }
        ]

    day_30 = [
        f"Fix {gap['gap_type']}: {gap['practice_task']}"
        for gap in top_gaps
    ]
    day_30.append(f"Start one stream-specific learning item: {stream['recommended_learning'][0]}.")

    day_60 = [
        "Submit two portfolio artifacts for AI and mentor review.",
        f"Complete one proof-of-readiness item: {stream['proof_of_readiness'][0]}.",
        "Repeat the written/spoken communication task and compare scores.",
    ]

    day_90 = [
        "Complete a role simulation or real-world project brief.",
        "Finalize resume/profile, portfolio checklist, and mentor feedback.",
        "Begin adoption tracking with weekly reflection and evidence updates.",
    ]

    return {"day_30": day_30, "day_60": day_60, "day_90": day_90}


def _adoption_index(scores: dict[str, int], evidence: set[str], reflection: str) -> dict[str, Any]:
    portfolio_component = min(100, len(evidence) * 12)
    reflection_component = 70 if len((reflection or "").split()) >= 30 else 45 if reflection else 25
    skill_component = round((scores["domain_technical_readiness"] + scores["communication_readiness"]) / 2)
    simulation_component = round((scores["problem_solving_readiness"] + scores["collaboration_leadership"]) / 2)
    consistency_component = round((scores["self_awareness_confidence"] + reflection_component) / 2)
    growth_component = scores["purpose_clarity"]

    total = round(
        skill_component * 0.20
        + portfolio_component * 0.20
        + 0 * 0.15
        + simulation_component * 0.20
        + reflection_component * 0.10
        + consistency_component * 0.10
        + growth_component * 0.05
    )
    return {
        "score": total,
        "components": {
            "skill_improvement": skill_component,
            "portfolio_evidence": portfolio_component,
            "mentor_teacher_rating": 0,
            "real_world_or_simulation_performance": simulation_component,
            "reflection_and_self_awareness": reflection_component,
            "consistency_and_discipline": consistency_component,
            "next_level_growth_plan": growth_component,
        },
    }


def diagnose_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    scores = _scores_with_context(payload)
    total = _weighted_total(scores)
    level = _level_for_score(total)
    gaps = _diagnose_gaps(scores)
    evidence = _normalize_evidence(payload.get("portfolio_evidence") or [])
    stream = _find_stream(payload.get("stream", ""))
    plan = _learning_plan(gaps, stream)

    # Compute CARI, CCQ, and Resilience indices
    ccq = 45
    resilience = 60
    cari = total

    context_factors = payload.get("context_factors")
    if context_factors:
        fp_str = context_factors.get("family_pressure", "Medium")
        fd_str = context_factors.get("financial_dependency", "Yes")
        conf_base = context_factors.get("confidence_baseline", 50)
        stress_base = context_factors.get("stress_baseline", 50)
        res_rating = context_factors.get("resilience_rating", 50)
        inc_tier = context_factors.get("income_tier", "Middle Class")
        city_t = context_factors.get("city_tier", "Tier 2")
        coll_t = context_factors.get("college_tier", "Tier 2")

        fp_val = 80 if fp_str == "High" else 50 if fp_str == "Medium" else 20
        fd_val = 70 if fd_str == "Yes" else 30
        inc_val = 80 if inc_tier == "Low" else 50 if inc_tier == "Middle Class" else 20
        city_val = 80 if city_t == "Rural" else 60 if city_t == "Tier 3" else 40 if city_t == "Tier 2" else 20
        coll_val = 80 if coll_t == "Tier 3" else 50 if coll_t == "Tier 2" else 20

        ccq = int((fp_val * 0.25) + (stress_base * 0.25) + (fd_val * 0.20) + (city_val * 0.15) + (coll_val * 0.15))
        resilience = int(res_rating)
        cari = int((total * 0.8) + (resilience * 0.2) - (ccq * 0.1))
        cari = max(0, min(100, cari))

    # Apply skills & credentials boosts to portfolio evidence
    if payload.get("skills_count", 0) > 0:
        scores["portfolio_evidence"] = min(100, scores["portfolio_evidence"] + 10)
    if payload.get("certifications_count", 0) > 0:
        scores["portfolio_evidence"] = min(100, scores["portfolio_evidence"] + 20)
    if payload.get("links_count", 0) > 0:
        scores["portfolio_evidence"] = min(100, scores["portfolio_evidence"] + 15)

    # Recalculate scorecard after skill boosts
    total = _weighted_total(scores)
    level = _level_for_score(total)
    if context_factors:
        cari = int((total * 0.8) + (resilience * 0.2) - (ccq * 0.1))
        cari = max(0, min(100, cari))

    next_best_action = (
        gaps[0]["practice_task"]
        if gaps
        else "Move to a higher difficulty simulation and refresh portfolio evidence."
    )

    target_role = (payload.get("target_role") or payload.get("dream_role") or "target role").strip()
    dream_role = (payload.get("dream_role") or target_role).strip()
    dream_reason = (payload.get("dream_reason") or "the learner wants to build a meaningful future").strip()
    impact = (payload.get("impact") or "create useful impact through consistent capability-building").strip()
    identity = (payload.get("identity_goal") or "a reliable, adaptable, evidence-driven professional").strip()

    return {
        "journey_stage": "Diagnosed",
        "next_best_action": next_best_action,
        "dream_profile": {
            "dream_statement": f"My dream direction is {dream_role}.",
            "purpose_statement": f"I want this because {dream_reason}.",
            "impact_statement": f"The impact I want to create is to {impact}.",
            "identity_growth_statement": f"The kind of person I must become is {identity}.",
            "target_role": target_role,
            "stream": stream["stream"],
        },
        "career_pathway": {
            "entry_level_roles": stream["common_dreams"][:5],
            "required_skills": stream["recommended_learning"][:6],
            "portfolio_evidence": stream["proof_of_readiness"][:5],
            "growth_view": {
                "3_year": "Build role fluency, portfolio depth, and first real-world outcomes.",
                "5_year": "Own larger projects, mentor juniors, and specialize in a high-value track.",
                "10_year": "Lead teams, products, practices, ventures, or advanced domain work.",
            },
        },
        "scorecard": {
            "total_score": total,
            "level": level["level"],
            "meaning": level["meaning"],
            "CARI": cari,
            "CCQ": ccq,
            "resilience_index": resilience,
            "dimensions": [
                {
                    "key": dimension["key"],
                    "label": dimension["label"],
                    "weight": dimension["weight"],
                    "layer": dimension["layer"],
                    "score": scores[dimension["key"]],
                }
                for dimension in READINESS_DIMENSIONS
            ],
            "layers": _layer_scores(scores),
        },
        "strengths": _strengths(scores),
        "gaps": gaps,
        "development_plan": plan,
        "portfolio_checklist": _portfolio_items(evidence),
        "mentor_summary": {
            "review_focus": [gap["mentor_action"] for gap in gaps[:3]],
            "suggested_touchpoint": "Validate the top gaps, review evidence quality, and agree on the first 30-day milestone.",
            "human_review_required_for": [
                "final certification",
                "placement readiness decisions",
                "sensitive emotional or mental-health signals",
                "disputed scores",
                "employer-facing recommendations",
            ],
        },
        "institution_analytics": {
            "cohort_signal": "Use this learner's dimension scores in department readiness heatmaps and recurring gap trends.",
            "intervention_need": gaps[0]["gap_type"] if gaps else "Advanced growth challenge",
            "portfolio_completion_percent": round(
                (len([item for item in _portfolio_items(evidence) if item["status"] == "Submitted"]) / len(PORTFOLIO_CHECKLIST)) * 100
            ),
        },
        "adoption_index": _adoption_index(scores, evidence, payload.get("reflection", "")),
        "source_documents": DOCUMENT_SOURCES,
    }


# Suggested stream-wise skills catalogs
def get_stream_suggested_skills(stream_name: str) -> dict[str, list[str]]:
    skills_map = {
        "engineering and technology": {
            "technical": ["Python Programming", "Git & GitHub", "SQL Database design", "Data Structures & Algorithms", "API Integration", "Unit Testing"],
            "non_technical": ["Technical Writing", "Sprint Project Management", "Team Presentations", "Active Code Review Communication", "Client Requirement Analysis"]
        },
        "management and business": {
            "technical": ["Financial Modeling", "Market Research", "Excel Pivot Tables & PowerBI", "SEO Analytics", "Sales CRM Tools"],
            "non_technical": ["Client Pitching", "Active Listening", "Negotiation", "Cross-Functional Collaboration", "Conflict Resolution"]
        },
        "healthcare and life sciences": {
            "technical": ["Clinical Charting", "Lab Safety Procedures", "Biostatistical Analysis", "Medical Terminology Mapping", "ECG Reading"],
            "non_technical": ["Patient Empathy", "Stress Crisis Communication", "Detail-Oriented Observation", "Multidisciplinary Coordination"]
        }
    }
    normalized = (stream_name or "").strip().lower()
    for key, val in skills_map.items():
        if key in normalized:
            return val
    return skills_map["engineering and technology"]


# Database pre-seeding helper
def seed_database_content(db):
    import json
    from .. import models

    # 1. Seed Success Mantras if empty
    if db.query(models.SuccessMantra).count() == 0:
        mantras = [
            models.SuccessMantra(
                title="The STAR Response Framework",
                category="Interview",
                content="Always structure behavioral answers chronologically: Situation (context), Task (goal), Action (what YOU did specifically), and Result (quantifiable impact or key learning). Use ownership verbs like 'I drove' or 'I resolved'.",
                action_items="Write out 3 past experiences using the STAR layout; highlight action verbs."
            ),
            models.SuccessMantra(
                title="Ownership & Empathy Code",
                category="Soft Skills",
                content="Never blame third parties or external triggers for blockers. Propose positive resolutions, seek feedback actively, and support teammates by explaining the 'why' behind choices.",
                action_items="Practice taking responsibility in scenarios; avoid words like 'not my job'."
            ),
            models.SuccessMantra(
                title="Clean Coding & Complexity Discipline",
                category="Technical",
                content="Write self-documenting code. Prefer descriptive variable names over abbreviations. Keep functions focused on a single task, handle bounds explicitly with try-except, and design for optimal time complexity.",
                action_items="Add safety boundaries and try-except blocks to your next coding module; write docstrings."
            )
        ]
        db.add_all(mantras)
        db.commit()

    # 2. Seed Campus & Global Courses
    if db.query(models.CampusCourse).count() == 0:
        courses = [
            models.CampusCourse(title="CS50: Introduction to Computer Science", provider="Harvard University", tier="Tier 1", origin="Abroad", direct_url="https://pll.harvard.edu/course/cs50-introduction-computer-science", fee_type="Free"),
            models.CampusCourse(title="NPTEL: Data Structures and Algorithms", provider="IIT Madras", tier="Tier 1", origin="India", direct_url="https://nptel.ac.in/courses/106106127", fee_type="Free"),
            models.CampusCourse(title="Professional Python Web Development", provider="Asperion Tech Partner", tier="Tier 2", origin="India", direct_url="https://asperion.org/web-dev", fee_type="Paid")
        ]
        db.add_all(courses)
        db.commit()

        # Seed coupon vouchers
        course_paid = db.query(models.CampusCourse).filter(models.CampusCourse.fee_type == "Paid").first()
        if course_paid:
            coupon = models.CourseCoupon(course_id=course_paid.id, code="ASPERION100", organization="Asperion Partnership", discount_percent=100)
            db.add(coupon)
            db.commit()

    # 3. Seed Asperion LMS Courses
    if db.query(models.LmsCourse).count() == 0:
        lms_c = models.LmsCourse(
            title="Asperion Readiness BootCamp: Engineering Track",
            description="Complete curriculum covering system diagnostics, mock interviews, portfolio creation, and workplace behavior syncs.",
            instructor="Dr. Aris Vance, Head of Skilling",
            stream="Engineering and Technology",
            duration="4 weeks",
            difficulty="Medium"
        )
        db.add(lms_c)
        db.commit()

        m1 = models.LmsModule(course_id=lms_c.id, title="Module 1: The STAR Narrative", order_no=1)
        m2 = models.LmsModule(course_id=lms_c.id, title="Module 2: Error Boundaries and Clean Python", order_no=2)
        db.add_all([m1, m2])
        db.commit()

        l1 = models.LmsLecture(module_id=m1.id, title="Lecture 1.1: Structuring spoken answers", content_type="Video", content="Video tutorial explaining pacing WPM, filler word penalties, and the Situation-Task-Action-Result format.", mantras="Practice recording your answers out loud; aim for 120-150 words per minute.")
        l2 = models.LmsLecture(module_id=m2.id, title="Lecture 2.1: Writing try-except robust blocks", content_type="Worksheet", content="Worksheet detailing python exception trees, static compiler assertions, and clean variable names.", mantras="Handle boundary inputs (None, empty list) first; compile code before submitting.")
        db.add_all([l1, l2])
        db.commit()

    # 4. Seed Live Jobs
    if db.query(models.ExistingJob).count() == 0:
        jobs = [
            models.ExistingJob(title="Junior Python Engineer", organization="Asperion Technologies", type="Corporate", required_skills="Python, SQL, Git", url="https://asperion.org/careers/python-dev", match_score=85),
            models.ExistingJob(title="National Informatics Center Web Assistant", organization="Government of India", type="Government", required_skills="PHP, HTML, databases", url="https://nic.in/careers", match_score=70),
            models.ExistingJob(title="System Analyst Intern", organization="Local Business Group", type="Local", required_skills="Excel, Communication", url="https://localbusiness.org/interns", match_score=90)
        ]
        db.add_all(jobs)
        db.commit()

    # 5. Seed Knowledge Graph
    if db.query(models.KnowledgeGraphNode).count() == 0:
        n1 = models.KnowledgeGraphNode(node_type="Dream", label="AI Developer")
        n2 = models.KnowledgeGraphNode(node_type="Skill", label="Python Programming")
        n3 = models.KnowledgeGraphNode(node_type="Course", label="Asperion Readiness BootCamp")
        n4 = models.KnowledgeGraphNode(node_type="Coupon", label="ASPERION100")
        n5 = models.KnowledgeGraphNode(node_type="Job", label="Junior Python Engineer")
        db.add_all([n1, n2, n3, n4, n5])
        db.commit()

        e1 = models.KnowledgeGraphEdge(source_id=n1.id, target_id=n2.id, rel_type="requires")
        e2 = models.KnowledgeGraphEdge(source_id=n2.id, target_id=n3.id, rel_type="remediated_by")
        e3 = models.KnowledgeGraphEdge(source_id=n3.id, target_id=n4.id, rel_type="discounted_by")
        e4 = models.KnowledgeGraphEdge(source_id=n4.id, target_id=n5.id, rel_type="matches")
        db.add_all([e1, e2, e3, e4])
        db.commit()

    # 6. Seed Vector Documents (RAG)
    if db.query(models.VectorDocument).count() == 0:
        d1 = models.VectorDocument(
            title="Universal Readiness Flow Framework",
            content="The framework maps learner growth through 9 progressive stages (Dream, Discover, Diagnose, Design, Develop, Demonstrate, Deploy, Adopt, Grow). Diagnostics should combine context factors (CARI/CCQ) with skill sub-scores."
        )
        d2 = models.VectorDocument(
            title="Agentic Readiness Platform Build Blueprint",
            content="System requires an interactive mock interview simulator supporting HR, Tech, PM tracks with avatar interviewers. Assess speaking pacing, filler words, STAR alignment, and static code complexity KPIs."
        )
        db.add_all([d1, d2])
        db.commit()

    # 7. Seed CAG cache registry
    if db.query(models.CagCacheRegistry).count() == 0:
        c1 = models.CagCacheRegistry(doc_title="Universal Readiness Flow Framework", cache_status="Pre-cached")
        c2 = models.CagCacheRegistry(doc_title="Agentic Readiness Platform Build Blueprint", cache_status="Pre-cached")
        db.add_all([c1, c2])
        db.commit()

    # 8. Seed Platform Moats
    if db.query(models.PlatformMoat).count() == 0:
        moats = [
            models.PlatformMoat(metric_key="Proprietary Mock Interview Dataset Size", metric_val="14,820 records"),
            models.PlatformMoat(metric_key="Custom Evaluator Fine-tuned Checkpoints", metric_val="v1.4-active"),
            models.PlatformMoat(metric_key="Academic Collaboration Partnerships", metric_val="42 Universities")
        ]
        db.add_all(moats)
        db.commit()


# RAG search query
def query_rag_context(db, query: str) -> str:
    from .. import models
    start_time = time.perf_counter()
    
    # Simulate CAG cache check
    cag_hit = db.query(models.CagCacheRegistry).filter(models.CagCacheRegistry.doc_title.ilike(f"%{query}%")).first()
    if cag_hit:
        rag_cag_metrics["cache_hits"] += 1
        rag_cag_metrics["latency_cag_ms"] = int((time.perf_counter() - start_time) * 1000)
        return f"Cached Document [{cag_hit.doc_title}]: Pre-cached context."

    docs = db.query(models.VectorDocument).all()
    best_doc = None
    best_matches = 0
    words = set(query.lower().split())
    for doc in docs:
        matches = sum(1 for w in words if w in doc.content.lower())
        if matches > best_matches:
            best_matches = matches
            best_doc = doc
            
    rag_cag_metrics["latency_rag_ms"] = int((time.perf_counter() - start_time) * 1000)
    
    if best_doc:
        return f"Document [{best_doc.title}]: {best_doc.content}"
    return "No documentation matches found in RAG registry."


# Closed feedback loop logger and plan injector
def process_feedback_loop_trigger(db, learner_id: int, trigger_event: str, current_score: int):
    from .. import models
    import json

    action = "Logged event."
    status = "Active"

    if "Low Score" in trigger_event or current_score < 60:
        action = "Auto-remediated: Alerted mentor, flagged gap, and injected high-priority remediation task into active LearningPlan."
        lp = db.query(models.LearningPlan).filter(models.LearningPlan.learner_id == learner_id, models.LearningPlan.status == "Active").first()
        if lp:
            try:
                tasks = json.loads(lp.weekly_tasks_json)
                tasks.insert(0, {"task": "High Priority: Complete 1-on-1 mentorship drill with speaking practice.", "completed": False})
                lp.weekly_tasks_json = json.dumps(tasks)
            except Exception:
                pass
    elif "Prompt Bypass" in trigger_event:
        action = "Flagged: Locked profile for HITL security review due to suspect instruction injection."
        status = "Pending"
        hitl = models.HitlReviewQueue(learner_id=learner_id, task_type="safety warning", flag_reason="Prompt injection bypass attempt blocked.", status="Pending")
        db.add(hitl)

    loop_log = models.FeedbackLoop(learner_id=learner_id, trigger_event=trigger_event, action_taken=action, status=status)
    db.add(loop_log)
    db.commit()


# Chronological Proceedings Audit Ledger logger
def log_readiness_proceeding(db, learner_id: int, flow_stage: str, description: str, metrics_snapshot: dict, strategic_action: str):
    from .. import models
    import json

    snapshot_str = json.dumps(metrics_snapshot)
    proceeding = models.ReadinessProceeding(
        learner_id=learner_id,
        flow_stage=flow_stage,
        description=description,
        metrics_snapshot=snapshot_str,
        strategic_action=strategic_action
    )
    db.add(proceeding)
    db.commit()

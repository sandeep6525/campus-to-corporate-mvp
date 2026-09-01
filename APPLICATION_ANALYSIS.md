# Campus-to-Corporate MVP - Application Analysis

## **Overview**
This is an **AI-powered Campus-to-Corporate Soft-Skills Interview Platform** called **"AspireOS ReadyFlow AI Platform"**. It's designed to help students and fresh graduates prepare for corporate roles by conducting mock interviews and evaluating their soft skills, technical knowledge, and professional readiness.

---

## **Purpose & Use Cases**

The application serves as:

1. **Mock Interview Platform** - Simulates real job interviews with AI-generated questions
2. **Soft Skills Assessor** - Evaluates communication clarity, confidence, and professionalism
3. **Career Readiness Engine** - Maps students' skills, certifications, and experience to career pathways
4. **Personalized Learning Platform** - Generates personalized learning plans and gap diagnoses
5. **Mentor & Collaboration Hub** - Connects learners with mentors and peers

---

## **Key Features**

### **Core Interview System**
- **Question Generation**: Generates 5 contextual interview questions based on role, experience level, and stream
- **Multi-Modal Responses**: Accepts typed text, audio, and video answers
- **Media Transcription**: Converts speech to text using OpenAI API (with fallback mode)
- **Answer Evaluation**: Analyzes clarity, confidence, filler words, and technical depth

### **Scoring & Analytics**
Evaluates responses on:
- **Clarity Score** - How well articulated the response is
- **Confidence Score** - Perceived confidence level
- **Overall Score** - Composite evaluation
- **Filler Word Count** - Tracks "um," "uh," "like," "basically," etc.
- **Technical Fluency** - For technical roles (code complexity, syntax validation)
- **Behavioral Metrics**:
  - Growth Mindset
  - Ownership
  - Collaborative Empathy
  - Stress Resilience
  - Professional Integrity

### **Learner Profile & Career Mapping**
- Comprehensive learner profiles including:
  - Skills (with proficiency levels)
  - Certifications
  - Work experience
  - Dream pathways and career goals
  - Dream statements and purpose statements
  - Context factors (family pressure, financial dependency, resilience)

### **Advanced Features**
- **Dream Pathway Mapping** - Maps 3-year, 5-year, and 10-year career goals
- **Career Shift Matrix** - Analyzes transferable skills for career transitions
- **Readiness Scorecard** - Weighted assessment of job readiness
- **Gap Diagnosis** - Identifies skill gaps and recommends improvements
- **Learning Plans** - Generates personalized 30/60/90 day roadmaps
- **Portfolio Checklist** - Tracks certifications, projects, and achievements

### **LMS & Collaboration**
- Learning modules and courses
- Video lectures with transcripts
- Student collaboration forums
- LMS enrollment and progress tracking

### **Knowledge Graph & RAG**
- Vector documents for semantic search
- Knowledge graph nodes and edges
- RAG (Retrieval Augmented Generation) for context-aware suggestions

### **Security & Audit**
- AI audit logs for transparency
- HITL (Human-in-the-Loop) review queue
- Security policy logs
- Feedback loop system for continuous improvement

---

## **Technology Stack**

| Layer | Technology |
|-------|-----------|
| **Backend Framework** | FastAPI (Python) |
| **Web Server** | Uvicorn |
| **Database** | SQLite with SQLAlchemy ORM |
| **Frontend** | Jinja2 Templates, JavaScript, CSS |
| **AI/ML** | OpenAI API (GPT-4o-mini for questions/evaluation, GPT-4o for transcription) |
| **File Management** | Python Multipart for media uploads |
| **Database Migrations** | Alembic |
| **Config Management** | Pydantic & python-dotenv |

---

## **Project Structure**

```
campus_corporate_mvp/
├── app/
│   ├── main.py                    # FastAPI app & routes
│   ├── db.py                      # SQLAlchemy setup
│   ├── models.py                  # Database models (30+ tables)
│   ├── schemas.py                 # Pydantic schemas
│   ├── config.py                  # Configuration
│   ├── services/
│   │   ├── ai_provider.py         # OpenAI integration
│   │   ├── evaluator.py           # Answer evaluation logic
│   │   ├── question_bank.py       # Question generation
│   │   └── readiness_engine.py    # Career readiness features
│   ├── templates/
│   │   └── index.html             # Frontend HTML
│   └── static/
│       ├── app.js                 # Frontend JavaScript
│       └── styles.css             # Styling
├── data/
│   └── uploads/                   # Media uploads directory
├── scripts/
│   └── upgrade_db.py              # Database migration scripts
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # Documentation
```

---

## **Key Database Models (30+ Tables)**

### **User & Profile Management**
- `User` - Platform users (Learner, Mentor, Institution, Employer)
- `LearnerProfile` - Student profiles with background, stream, experience
- `ContextFactors` - Socioeconomic & psychological context (family pressure, resilience, etc.)

### **Skills & Certifications**
- `StudentSkill` - Technical/Non-technical skills with proficiency
- `StudentCertification` - Verified credentials
- `StudentLink` - Portfolio links (GitHub, LinkedIn, Behance, etc.)

### **Career Planning**
- `CareerShiftMatrix` - Career transition analysis
- `DreamPathway` - 3/5/10-year career goals
- `ReadinessScorecard` - Job readiness evaluation
- `GapReport` - Skill gap analysis
- `LearningPlan` - Personalized learning roadmap
- `SuccessMantra` - Motivational/personal mantras

### **Interview System**
- `Session` - Interview session tracking
- `Question` - Interview questions
- `Answer` - Learner responses
- `MediaAsset` - Audio/video recordings

### **LMS & Learning**
- `LmsCourse`, `LmsModule`, `LmsLecture` - Course content
- `LmsEnrollment` - Student enrollments
- `LmsCollaborationPost` - Forum/discussion posts

### **Advanced Features**
- `VectorDocument` - RAG documents
- `KnowledgeGraphNode`, `KnowledgeGraphEdge` - Knowledge representation
- `MentorSession` - Mentor meetings
- `ExistingJob` - Job history
- `InstitutionalCollaboration` - School/employer partnerships
- `HitlReviewQueue` - Human review items
- `FeedbackLoop` - System feedback for continuous learning
- `AiAuditLog` - AI decision audit trail
- `PlatformMoat` - Competitive advantages tracking

---

## **API Endpoints**

### **Interview Flow**
- `POST /api/sessions` - Create new interview session
- `GET /api/sessions/{session_id}` - Get session details
- `GET /api/sessions/{session_id}/current-question` - Get next question
- `POST /api/sessions/{session_id}/answers` - Submit text answer
- `POST /api/sessions/{session_id}/answers/media` - Upload audio/video
- `POST /api/sessions/{session_id}/answers/{answer_id}/media/analytics` - Analyze media response
- `GET /api/sessions/{session_id}/report` - Get interview report

### **Career & Readiness**
- `GET /api/framework` - Get readiness framework
- `POST /api/readiness/diagnose` - Get gap diagnosis

### **System**
- `GET /health` - Health check

---

## **Workflow - How It Works**

1. **User Registration** → Creates profile with name, target role, experience level
2. **Session Creation** → System generates interview session
3. **Question Generation** → AI creates 5 contextual questions (or fallback deterministic questions)
4. **Answer Collection** → User answers via text, audio, or video
5. **Media Processing** → Audio/video transcribed to text (optional)
6. **Evaluation** → AI evaluates clarity, confidence, technical knowledge
7. **Report Generation** → Dashboard shows scores, strengths, improvement areas
8. **Career Mapping** → System maps to dream pathways and learning plans

---

## **AI Integration**

### **OpenAI Features** (Optional)
- **Question Generation** → GPT-4o-mini generates contextual interview questions
- **Answer Evaluation** → Analyzes responses for clarity, confidence, technical depth
- **Speech Transcription** → GPT-4o-transcribe converts audio to text

### **Fallback Mode** (No API Key)
- Uses deterministic question bank (pre-defined questions)
- Evaluates typed answers based on heuristics (filler word count, sentence length)
- Disables media transcription

---

## **Why This Was Created**

This MVP addresses the **campus-to-corporate transition gap**:
- Students lack real interview experience
- Limited access to personalized career coaching
- No standardized way to assess soft skills
- Need for personalized career pathways based on individual context

The platform combines:
- **Mock interviews** for skill practice
- **AI evaluation** for objective feedback
- **Learner context** (socioeconomic factors, resilience, goals)
- **Career mapping** to match capabilities with opportunities
- **Mentorship** and peer collaboration
- **Continuous learning** through LMS integration

---

## **What Makes It Special**

✅ **Full-Stack MVP** - Production-ready FastAPI backend + frontend
✅ **AI-Powered** - OpenAI integration with intelligent fallback
✅ **Comprehensive** - 30+ database tables for holistic learner tracking
✅ **Offline-Capable** - Works without API key using deterministic fallback
✅ **Multi-Modal** - Supports text, audio, and video answers
✅ **Career Intelligence** - Dream pathways, gap diagnosis, learning plans
✅ **Mentorship-Ready** - Mentor sessions, collaboration, HITL review

---

## **Environment Variables Required**

```env
OPENAI_API_KEY=sk-...          # Optional for AI features
OPENAI_MODEL=gpt-4o-mini       # Question generation model
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-transcribe
UPLOADS_DIR=./data/uploads     # Media storage
```

---

## **Quick Start**

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
# Open http://127.0.0.1:8000
```

---

**Created on:** August 31, 2026
**Framework:** Campus-to-Corporate AI MVP
**Status:** Production-Ready MVP

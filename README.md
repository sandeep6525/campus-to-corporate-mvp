# Campus-to-Corporate AI MVP

A runnable end-to-end MVP for an AI-powered campus-to-corporate soft-skills platform.

## What this MVP includes

- FastAPI backend
- SQLite database
- Browser-based frontend
- Mock interview flow
- Question generation
- Answer evaluation
- Communication analysis
- Final report dashboard
- Optional OpenAI integration
- Audio and video response recording with speech transcription
- Media upload support with playback and transcript-backed scoring
- Safe offline fallback mode for typed text when no API key is configured
- Extracted readiness framework from the provided Word documents
- Dream mapping, weighted readiness scorecard, gap diagnosis, portfolio checklist, and 30/60/90 plan generation
- Framework, capability, roadmap, and current codebase map endpoints

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # Windows
# or: cp .env.example .env  # macOS / Linux
uvicorn app.main:app --reload
```

Open:
`http://127.0.0.1:8000`

## Environment variables

Create a `.env` file from `.env.example`.

- `OPENAI_API_KEY` = optional
- `OPENAI_MODEL` = optional, defaults to `gpt-4o-mini`
- `OPENAI_TRANSCRIPTION_MODEL` = optional, defaults to `gpt-4o-transcribe`
- `UPLOADS_DIR` = optional, defaults to `./data/uploads`

If no API key is set, the app uses a deterministic fallback engine for written answers and disables transcription.

## Product flow

1. User enters name, target role, experience level
2. System creates interview session
3. System generates 5 questions
4. User answers one by one
5. System evaluates each answer
6. Final dashboard shows:
   - overall score
   - clarity
   - confidence
   - filler-word count
   - strengths
   - improvement areas
   - recommended next steps

## Project structure

```text
campus_corporate_mvp/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── config.py
│   ├── services/
│   │   ├── ai_provider.py
│   │   ├── question_bank.py
│   │   └── evaluator.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── app.js
│       └── styles.css
├── data/
├── requirements.txt
├── .env.example
└── README.md
```

## API endpoints

- `GET /health`
- `POST /api/sessions`
- `GET /api/sessions/{session_id}`
- `GET /api/sessions/{session_id}/current-question`
- `POST /api/sessions/{session_id}/answers`
- `POST /api/sessions/{session_id}/answers/media`
- `POST /api/sessions/{session_id}/answers/{answer_id}/media/analytics`
- `GET /api/sessions/{session_id}/report`
- `GET /api/framework`
- `POST /api/readiness/diagnose`
- `GET /api/system/codebase`

## Document extraction

The provided `.docx` files were extracted into Markdown for implementation traceability:

- `../docs_extracted/Universal Readiness Flow Framework.md`
- `../docs_extracted/Agentic Readiness Platform Build Blueprint.md`

The app exposes the extracted product model through `/api/framework` and uses it in `app/services/readiness_engine.py`.

## Notes

- This is intentionally lean for MVP speed.
- Speech-to-text and authentication can be added next.
- The app now stores media assets separately from text answers, making playback analytics and media metadata production-ready.
- The readiness layer implements the first-build scope from the blueprint while keeping auth, employer marketplace, and advanced LMS integrations as future modules.
- To productionize:
  - switch SQLite to Postgres
   - add difficulty modes: `simple`, `medium`, `high`, and `stress` with real-time stress timers and media-backed scoring
  - add user auth
  - add Redis
  - add observability
  - deploy behind a reverse proxy

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from uuid import uuid4
from openai import OpenAI
from fastapi import UploadFile
from ..config import settings
from .question_bank import generate_fallback_questions
from .evaluator import score_text, EvaluationResult


def has_openai() -> bool:
    return bool(settings.openai_api_key)


def generate_questions(role: str, experience: str, difficulty: str = "medium", track: str = "HR & Behavioral") -> list[str]:
    if not has_openai():
        return generate_fallback_questions(role, experience, difficulty)

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = f"""
You are an expert campus-to-corporate interviewer.
Generate exactly 5 interview questions for a candidate.

Role: {role}
Experience Level: {experience}
Difficulty: {difficulty}
Interview Track: {track}

Requirements:
- return only valid JSON
- schema: {{"questions": ["q1","q2","q3","q4","q5"]}}
- questions must assess communication, professionalism, teamwork, adaptability, and track-specific skills (e.g. coding for tech track, behavioral scenarios for HR track).
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You generate interview questions in strict JSON."},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    payload = json.loads(content or "{}")
    questions = payload.get("questions", [])
    return questions[:5] if questions else generate_fallback_questions(role, experience, difficulty)


def save_media_file(session_id: int, question_id: int, upload_file: UploadFile, media_type: str) -> tuple[str, str]:
    uploads_root = Path(settings.uploads_dir).resolve()
    target_dir = uploads_root / str(session_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = upload_file.filename or ("recording.webm" if media_type == "video" else "recording.wav")
    extension = Path(filename).suffix or (".webm" if media_type == "video" else ".wav")
    safe_name = f"q{question_id}-{uuid4().hex}{extension}"
    target_path = target_dir / safe_name

    with target_path.open("wb") as out_file:
        shutil.copyfileobj(upload_file.file, out_file)

    relative_url = f"/uploads/{session_id}/{safe_name}"
    return str(target_path), relative_url


def transcribe_media(file_path: str) -> str:
    if not has_openai():
        raise RuntimeError("OpenAI key required for speech transcription.")

    client = OpenAI(api_key=settings.openai_api_key)

    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=settings.openai_transcription_model,
            file=audio_file,
        )

    return getattr(response, "text", "").strip()


def evaluate_answer(
    question: str, 
    answer_text: str, 
    submitted_code: str | None = None, 
    is_stress: bool = False,
    rag_context: str | None = None
) -> EvaluationResult:
    if not has_openai():
        return score_text(answer_text, submitted_code, is_stress)

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = f"""
You are an interview evaluator for a campus-to-corporate skills platform.

RAG System Context Info:
{rag_context or "No additional documentation details."}

Question:
{question}

Candidate Answer:
{answer_text}

Submitted Code (if any):
{submitted_code or "No code submitted."}

Evaluate the answer and return only valid JSON with this schema:
{{
  "score_overall": 0-100 integer,
  "score_clarity": 0-100 integer,
  "score_confidence": 0-100 integer,
  "filler_word_count": integer,
  "strengths": ["...","...","..."],
  "improvements": ["...","...","..."],
  "feedback": "2-4 sentence actionable feedback",
  "code_time_complexity": "O(1)/O(N)/O(N^2)/etc" (or null if no code),
  "code_space_complexity": "O(1)/O(N)/etc" (or null if no code),
  "code_cleanliness_score": 0-100 integer (or null if no code),
  "code_error_resilience": 0-100 integer (or null if no code),
  "code_syntax_passes": true/false (or null if no code),
  "technical_fluency": 0-100 integer,
  "non_technical_communication": 0-100 integer,
  "growth_mindset": 0-100 integer,
  "ownership": 0-100 integer,
  "collaborative_empathy": 0-100 integer,
  "stress_resilience": 0-100 integer,
  "professional_integrity": 0-100 integer
}}

Scoring focus:
- clarity
- confidence
- structure (STAR model alignment)
- technical fluency
- non-technical communication
- coding syntax, space-time complexities, error robustness, naming clean patterns (if code is present)
- behavioral indices (growth mindset, ownership, collaborative empathy, stress resilience, integrity)
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a strict JSON evaluator."},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    payload = json.loads(content or "{}")

    return EvaluationResult(
        score_overall=int(payload.get("score_overall", 60)),
        score_clarity=int(payload.get("score_clarity", 60)),
        score_confidence=int(payload.get("score_confidence", 60)),
        filler_word_count=int(payload.get("filler_word_count", 0)),
        strengths=list(payload.get("strengths", []))[:3] or ["Shows effort and engagement."],
        improvements=list(payload.get("improvements", []))[:3] or ["Add more specific examples."],
        feedback=str(payload.get("feedback", "Practice structured and specific responses.")),
        code_time_complexity=payload.get("code_time_complexity"),
        code_space_complexity=payload.get("code_space_complexity"),
        code_cleanliness_score=payload.get("code_cleanliness_score"),
        code_error_resilience=payload.get("code_error_resilience"),
        code_syntax_passes=payload.get("code_syntax_passes"),
        technical_fluency=int(payload.get("technical_fluency", 55)),
        non_technical_communication=int(payload.get("non_technical_communication", 55)),
        growth_mindset=int(payload.get("growth_mindset", 55)),
        ownership=int(payload.get("ownership", 55)),
        collaborative_empathy=int(payload.get("collaborative_empathy", 55)),
        stress_resilience=int(payload.get("stress_resilience", 70)),
        professional_integrity=int(payload.get("professional_integrity", 90))
    )

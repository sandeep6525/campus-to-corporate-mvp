from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from openai import OpenAI
from google import genai
from fastapi import UploadFile

from ..config import settings
from .question_bank import generate_fallback_questions
from .evaluator import score_text, EvaluationResult


# ============================================================
# PROVIDER AVAILABILITY
# ============================================================

def has_openai() -> bool:
    return bool(settings.openai_api_key)


def has_gemini() -> bool:
    return bool(settings.gemini_api_key)


# ============================================================
# MOCK INTERVIEW - QUESTION GENERATION
# ============================================================

def generate_questions(
    role: str,
    experience: str,
    difficulty: str = "medium",
    track: str = "HR & Behavioral"
) -> list[str]:

    # ------------------------------------------------------------
    # Gemini not configured → local fallback
    # ------------------------------------------------------------
    if not has_gemini():
        print("Gemini key not configured. Using fallback questions.")

        return generate_fallback_questions(
            role,
            experience,
            difficulty
        )

    try:
        client = genai.Client(
            api_key=settings.gemini_api_key
        )

        prompt = f"""
You are an expert campus-to-corporate interviewer.

Generate exactly 5 interview questions for a candidate.

Role: {role}
Experience Level: {experience}
Difficulty: {difficulty}
Interview Track: {track}

Requirements:

- Return ONLY valid JSON.
- Do not use markdown.
- Do not include ```json.
- Do not include explanations outside the JSON.
- Do not duplicate questions.

The JSON schema must be:

{{
  "questions": [
    "q1",
    "q2",
    "q3",
    "q4",
    "q5"
  ]
}}

Question requirements:

- Questions must be relevant to the candidate's role.
- Assess communication and professionalism.
- Assess teamwork and collaboration.
- Assess adaptability and problem solving.
- Include track-specific skills.
- Match the candidate's experience level.
- Questions should progressively become more challenging.
"""

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        content = (response.text or "").strip()

        # --------------------------------------------------------
        # Remove markdown code fences if Gemini returns them
        # --------------------------------------------------------
        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        payload = json.loads(content or "{}")

        questions = payload.get("questions", [])

        # --------------------------------------------------------
        # Validate questions
        # --------------------------------------------------------
        if isinstance(questions, list):
            questions = [
                str(question).strip()
                for question in questions
                if str(question).strip()
            ]
        else:
            questions = []

        # --------------------------------------------------------
        # Gemini success
        # --------------------------------------------------------
        if len(questions) >= 5:
            print(
                "Gemini generated interview questions successfully."
            )

            return questions[:5]

        # --------------------------------------------------------
        # Gemini returned invalid/incomplete data
        # --------------------------------------------------------
        print(
            "Gemini returned fewer than 5 valid questions. "
            "Using fallback questions."
        )

        return generate_fallback_questions(
            role,
            experience,
            difficulty
        )

    except Exception as exc:

        # --------------------------------------------------------
        # Gemini API failure → local fallback
        # --------------------------------------------------------
        print(
            f"Gemini question generation unavailable: "
            f"{type(exc).__name__}: {exc}"
        )

        print(
            "Using local fallback interview questions."
        )

        return generate_fallback_questions(
            role,
            experience,
            difficulty
        )


# ============================================================
# MEDIA FILE STORAGE
# ============================================================

def save_media_file(
    session_id: int,
    question_id: int,
    upload_file: UploadFile,
    media_type: str
) -> tuple[str, str]:

    uploads_root = Path(
        settings.uploads_dir
    ).resolve()

    target_dir = uploads_root / str(session_id)

    target_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        upload_file.filename
        or (
            "recording.webm"
            if media_type == "video"
            else "recording.wav"
        )
    )

    extension = (
        Path(filename).suffix
        or (
            ".webm"
            if media_type == "video"
            else ".wav"
        )
    )

    safe_name = (
        f"q{question_id}-{uuid4().hex}{extension}"
    )

    target_path = target_dir / safe_name

    with target_path.open("wb") as out_file:
        shutil.copyfileobj(
            upload_file.file,
            out_file
        )

    relative_url = (
        f"/uploads/{session_id}/{safe_name}"
    )

    return str(target_path), relative_url


# ============================================================
# SPEECH TRANSCRIPTION
# ============================================================
# Keep OpenAI here for now.
# Gemini is being used for interview questions/evaluation.
# ============================================================

def transcribe_media(file_path: str) -> str:

    if not has_openai():
        raise RuntimeError(
            "OpenAI key required for speech transcription."
        )

    client = OpenAI(
        api_key=settings.openai_api_key
    )

    with open(file_path, "rb") as audio_file:

        response = client.audio.transcriptions.create(
            model=settings.openai_transcription_model,
            file=audio_file,
        )

    return getattr(
        response,
        "text",
        ""
    ).strip()


# ============================================================
# MOCK INTERVIEW - ANSWER EVALUATION
# ============================================================

def evaluate_answer(
    question: str,
    answer_text: str,
    submitted_code: str | None = None,
    is_stress: bool = False,
    rag_context: str | None = None
) -> EvaluationResult:

    # ------------------------------------------------------------
    # Gemini not configured → local evaluation
    # ------------------------------------------------------------
    if not has_gemini():

        print(
            "Gemini key not configured. "
            "Using local answer evaluation."
        )

        return score_text(
            answer_text,
            submitted_code,
            is_stress
        )

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    # ------------------------------------------------------------
    # Evaluation prompt
    # ------------------------------------------------------------

    prompt = f"""
You are a strict professional interview evaluator
for a campus-to-corporate skills platform.

Evaluate the candidate's answer carefully.

RAG System Context Info:
{rag_context or "No additional documentation details."}

Interview Question:
{question}

Candidate Answer:
{answer_text}

Submitted Code:
{submitted_code or "No code submitted."}

Stress Interview:
{"Yes" if is_stress else "No"}

Return ONLY valid JSON.

Do not use markdown.
Do not include ```json.
Do not include explanations outside the JSON.

The JSON schema must be:

{{
  "score_overall": 0,
  "score_clarity": 0,
  "score_confidence": 0,
  "filler_word_count": 0,

  "strengths": [
    "...",
    "...",
    "..."
  ],

  "improvements": [
    "...",
    "...",
    "..."
  ],

  "feedback": "2-4 sentence actionable feedback",

  "code_time_complexity": null,
  "code_space_complexity": null,
  "code_cleanliness_score": null,
  "code_error_resilience": null,
  "code_syntax_passes": null,

  "technical_fluency": 0,
  "non_technical_communication": 0,

  "growth_mindset": 0,
  "ownership": 0,
  "collaborative_empathy": 0,
  "stress_resilience": 0,
  "professional_integrity": 0
}}

Scoring rules:

1. score_overall
- Overall quality of the candidate's response.
- Range: 0-100.

2. score_clarity
- How clearly the candidate communicates.
- Range: 0-100.

3. score_confidence
- Confidence and decisiveness of the response.
- Range: 0-100.

4. filler_word_count
- Estimate filler words such as:
  um, uh, like, actually, basically, you know.
- Return an integer.

5. strengths
- Provide exactly 3 meaningful strengths.

6. improvements
- Provide exactly 3 actionable improvements.

7. feedback
- Give 2-4 sentences.
- Make the feedback specific to the candidate's answer.

8. STAR structure
For behavioral questions evaluate:
- Situation
- Task
- Action
- Result

9. technical_fluency
- Understanding of technical concepts.
- Range: 0-100.

10. non_technical_communication
- Ability to explain concepts clearly to non-technical people.
- Range: 0-100.

11. growth_mindset
- Evidence of learning and improvement.
- Range: 0-100.

12. ownership
- Responsibility for actions and outcomes.
- Range: 0-100.

13. collaborative_empathy
- Teamwork and understanding of others.
- Range: 0-100.

14. stress_resilience
- Ability to remain composed under pressure.
- Range: 0-100.

15. professional_integrity
- Honesty, responsibility and professional ethics.
- Range: 0-100.

Coding evaluation:

If submitted code exists:

- Analyze syntax.
- Determine time complexity.
- Determine space complexity.
- Evaluate code cleanliness.
- Evaluate error handling.
- Evaluate naming and structure.
- Set code_syntax_passes to true or false.

If no code exists:

- code_time_complexity = null
- code_space_complexity = null
- code_cleanliness_score = null
- code_error_resilience = null
- code_syntax_passes = null
"""

    # ------------------------------------------------------------
    # Try Gemini evaluation
    # ------------------------------------------------------------

    try:

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        content = (
            response.text or ""
        ).strip()

        # --------------------------------------------------------
        # Clean markdown JSON fences
        # --------------------------------------------------------

        if content.startswith("```"):

            content = (
                content
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        payload = json.loads(
            content or "{}"
        )

        print(
            "Gemini answer evaluation successful."
        )

    except Exception as exc:

        # --------------------------------------------------------
        # Gemini failed → local fallback
        # --------------------------------------------------------

        print(
            f"Gemini answer evaluation unavailable: "
            f"{type(exc).__name__}: {exc}"
        )

        print(
            "Using local fallback answer evaluation."
        )

        answer_clean = (
            answer_text or ""
        ).strip()

        answer_length = len(
            answer_clean
        )

        # --------------------------------------------------------
        # Basic local scoring
        # --------------------------------------------------------

        if answer_length == 0:

            base_score = 35
            clarity_score = 30
            confidence_score = 30

            feedback = (
                "No answer content was provided. "
                "Practice giving a clear and structured response."
            )

        elif answer_length < 40:

            base_score = 50
            clarity_score = 45
            confidence_score = 45

            feedback = (
                "Your answer is quite brief. "
                "Add specific details, examples, "
                "and explain your contribution."
            )

        elif answer_length < 150:

            base_score = 65
            clarity_score = 60
            confidence_score = 60

            feedback = (
                "Your response provides a reasonable starting point. "
                "Improve it by adding a specific example "
                "and clearer structure."
            )

        else:

            base_score = 75
            clarity_score = 72
            confidence_score = 70

            feedback = (
                "Your response contains useful detail. "
                "Continue improving structure, specificity, "
                "and measurable outcomes."
            )

        # --------------------------------------------------------
        # Local fallback payload
        # --------------------------------------------------------

        payload = {

            "score_overall": base_score,

            "score_clarity": clarity_score,

            "score_confidence": confidence_score,

            "filler_word_count": 0,

            "strengths": [
                "Attempted the interview question.",
                "Provided a direct response.",
                "Demonstrated engagement with the interview."
            ],

            "improvements": [
                "Add specific examples.",
                "Use a clear STAR-style structure.",
                "Explain your individual contribution and outcome."
            ],

            "feedback": feedback,

            "code_time_complexity": None,

            "code_space_complexity": None,

            "code_cleanliness_score": None,

            "code_error_resilience": None,

            "code_syntax_passes": None,

            "technical_fluency": base_score,

            "non_technical_communication": clarity_score,

            "growth_mindset": 60,

            "ownership": 60,

            "collaborative_empathy": 60,

            "stress_resilience": confidence_score,

            "professional_integrity": 80,
        }

    # ============================================================
    # STANDARD EVALUATION RESULT
    # ============================================================

    return EvaluationResult(

        score_overall=int(
            payload.get(
                "score_overall",
                60
            )
        ),

        score_clarity=int(
            payload.get(
                "score_clarity",
                60
            )
        ),

        score_confidence=int(
            payload.get(
                "score_confidence",
                60
            )
        ),

        filler_word_count=int(
            payload.get(
                "filler_word_count",
                0
            )
        ),

        strengths=(
            list(
                payload.get(
                    "strengths",
                    []
                )
            )[:3]

            or [
                "Shows effort and engagement."
            ]
        ),

        improvements=(
            list(
                payload.get(
                    "improvements",
                    []
                )
            )[:3]

            or [
                "Add more specific examples."
            ]
        ),

        feedback=str(
            payload.get(
                "feedback",
                "Practice structured and specific responses."
            )
        ),

        code_time_complexity=payload.get(
            "code_time_complexity"
        ),

        code_space_complexity=payload.get(
            "code_space_complexity"
        ),

        code_cleanliness_score=payload.get(
            "code_cleanliness_score"
        ),

        code_error_resilience=payload.get(
            "code_error_resilience"
        ),

        code_syntax_passes=payload.get(
            "code_syntax_passes"
        ),

        technical_fluency=int(
            payload.get(
                "technical_fluency",
                55
            )
        ),

        non_technical_communication=int(
            payload.get(
                "non_technical_communication",
                55
            )
        ),

        growth_mindset=int(
            payload.get(
                "growth_mindset",
                55
            )
        ),

        ownership=int(
            payload.get(
                "ownership",
                55
            )
        ),

        collaborative_empathy=int(
            payload.get(
                "collaborative_empathy",
                55
            )
        ),

        stress_resilience=int(
            payload.get(
                "stress_resilience",
                70
            )
        ),

        professional_integrity=int(
            payload.get(
                "professional_integrity",
                90
            )
        )
    )
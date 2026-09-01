DEFAULT_QUESTIONS = [
    "Tell me about yourself and walk me through your background.",
    "Why are you interested in this role?",
    "Describe a time you worked in a team to solve a problem.",
    "Tell me about a challenge you faced and how you handled it.",
    "What are your strengths, and what skill are you currently improving?",
]


ROLE_QUESTION_MAP = {
    "software engineer": [
        "Explain a project you built and the impact it created.",
        "How do you approach debugging when something breaks unexpectedly?",
        "Describe a time you collaborated with others on a technical task.",
        "How do you balance speed and code quality?",
        "What technology are you currently learning and why?",
    ],
    "data analyst": [
        "Describe a data project you worked on and the insight you delivered.",
        "How do you ensure data quality before drawing conclusions?",
        "Tell me about a time you explained data to a non-technical audience.",
        "How do you prioritize conflicting requests from stakeholders?",
        "What analytics tool do you use best and why?",
    ],
    "sales": [
        "How would you build trust with a new prospect?",
        "Tell me about a time you persuaded someone.",
        "How do you handle rejection and stay motivated?",
        "What would you do before your first client meeting?",
        "How do you balance relationship building with targets?",
    ],
}


def generate_fallback_questions(role: str, experience: str, difficulty: str = "medium") -> list[str]:
    normalized = role.strip().lower()
    base = DEFAULT_QUESTIONS
    for key, questions in ROLE_QUESTION_MAP.items():
        if key in normalized:
            base = questions
            break

    # Adjust by difficulty
    if difficulty == "simple":
        return [q + " (Keep answers concise and high-level.)" for q in base[:5]]
    if difficulty == "high":
        return [q + " (Include technical depth, metrics, and edge-cases.)" for q in base[:5]]
    if difficulty == "stress":
        # Stress test returns more rapid-fire prompts and one follow-up
        extra = ["Quick: summarize a failure and what you learned.", "Explain a technical trade-off in 30 seconds."]
        return (base[:4] + extra)[:5]
    # medium or default
    return base[:5]

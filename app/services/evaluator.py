from __future__ import annotations

from dataclasses import dataclass
import re


FILLERS = {"um", "uh", "like", "you know", "basically", "actually", "literally", "sort of", "kind of"}

@dataclass
class EvaluationResult:
    score_overall: int
    score_clarity: int
    score_confidence: int
    filler_word_count: int
    strengths: list[str]
    improvements: list[str]
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


def count_filler_words(text: str) -> int:
    lowered = text.lower()
    count = 0
    for filler in FILLERS:
        count += len(re.findall(r"\b" + re.escape(filler) + r"\b", lowered))
    return count


def sentence_count(text: str) -> int:
    return max(1, len([s for s in re.split(r"[.!?]+", text) if s.strip()]))


def parse_code_complexity(code: str) -> tuple[str, str, int, int, bool]:
    # Default variables
    time_comp = "O(1)"
    space_comp = "O(1)"
    cleanliness = 65
    resilience = 30
    syntax_passes = False

    if not code or len(code.strip()) < 5:
        return time_comp, space_comp, cleanliness, resilience, syntax_passes

    # Syntax compile check
    try:
        compile(code, "<string>", "exec")
        syntax_passes = True
    except Exception:
        syntax_passes = False

    # Time Complexity Heuristics
    # Nested loops
    if len(re.findall(r"\bfor\b.*\bfor\b", code, re.DOTALL)) > 0 or len(re.findall(r"for\s+\w+\s+in\s+.*:\s*\n\s+.*for\s+\w+", code)) > 0:
        time_comp = "O(N^2)"
    elif "for " in code or "while " in code:
        if "binary" in code.lower() or "search" in code.lower() or "/ 2" in code or "// 2" in code or ">>" in code:
            time_comp = "O(log N)"
        else:
            time_comp = "O(N)"

    # Space Complexity Heuristics
    if "list(" in code or "dict(" in code or "set(" in code or "append(" in code or "[]" in code or "{}" in code:
        if time_comp == "O(N^2)":
            space_comp = "O(N)"
        else:
            space_comp = "O(N)"
            
    # Cleanliness metrics (comments, docstrings, modularity)
    comments = len(re.findall(r"#.*", code))
    functions = len(re.findall(r"\bdef\s+\w+", code))
    
    if comments > 0:
        cleanliness += 15
    if functions > 0:
        cleanliness += 15
    # penalty for bad single char variable names (not loop indices like i, j)
    bad_vars = len(re.findall(r"\b[a-z]\s*=", code))
    if bad_vars > 2:
        cleanliness -= 15
        
    # Error resilience check (existence of try/except/catch)
    if "try:" in code and "except" in code:
        resilience = 90
    elif "if " in code and "None" in code or "assert" in code:
        resilience = 65

    return time_comp, space_comp, min(100, max(0, cleanliness)), min(100, max(0, resilience)), syntax_passes


def evaluate_behavioral_kpis(text: str, is_stress: bool = False) -> tuple[int, int, int, int, int]:
    text_lower = text.lower()
    
    # 1. Growth Mindset (learning vocabulary)
    growth_keywords = ["learn", "improve", "feedback", "mistake", "failing", "grow", "change", "adapt", "better"]
    growth_score = 45 + sum(10 for kw in growth_keywords if kw in text_lower)
    
    # 2. Ownership & Accountability (active action verbs vs blaming)
    ownership_keywords = ["i owned", "responsible", "my task", "i led", "accountable", "resolved", "i delivered", "my fault"]
    blame_keywords = ["not my job", "they didn't", "was forced to", "my manager made", "someone else"]
    ownership_score = 50 + sum(10 for kw in ownership_keywords if kw in text_lower) - sum(15 for kw in blame_keywords if kw in text_lower)

    # 3. Collaborative Empathy (teamwork)
    team_keywords = ["team", "we ", "collaborated", "support", "empath", "helped", "shared", "together", "cooperated"]
    empathy_score = 45 + sum(10 for kw in team_keywords if kw in text_lower)

    # 4. Stress Resilience (composed vocabulary, length drops)
    stress_score = 75
    if is_stress:
        if len(text.split()) < 20:
            stress_score = 40
        else:
            stress_score = 85

    # 5. Professional Integrity (evasive copy-paste check)
    integrity_score = 90
    if len(text.split()) < 6:
        integrity_score = 45
    # check repeating words block
    repeats = len(re.findall(r"(\b\w+\b)\s+\1", text_lower))
    if repeats > 2:
        integrity_score -= 30

    return (
        min(100, max(0, growth_score)),
        min(100, max(0, ownership_score)),
        min(100, max(0, empathy_score)),
        min(100, max(0, stress_score)),
        min(100, max(0, integrity_score))
    )


def score_text(answer_text: str, submitted_code: str | None = None, is_stress: bool = False) -> EvaluationResult:
    text = answer_text.strip()
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    fillers = count_filler_words(text)
    sentences = sentence_count(text)

    clarity = 40
    confidence = 40
    overall = 40
    strengths = []
    improvements = []

    # Text length evaluations
    if word_count >= 40:
        clarity += 15
        overall += 10
        strengths.append("Provides enough detail to evaluate the answer.")
    else:
        improvements.append("Add more depth with examples, actions, and results.")

    if word_count >= 80:
        clarity += 10
        overall += 10
        strengths.append("Demonstrates strong content depth.")
    else:
        improvements.append("Expand your answer using a clearer structure such as Situation, Action, Result.")

    # Sentence pace check
    avg_sentence_len = word_count / max(1, sentences)
    if 8 <= avg_sentence_len <= 22:
        clarity += 15
        strengths.append("Sentence flow is reasonably easy to follow.")
    else:
        improvements.append("Use shorter, clearer sentences to improve readability.")

    # Filler words penalty
    if fillers <= 2:
        confidence += 20
        overall += 10
        strengths.append("Uses very few filler words.")
    else:
        improvements.append("Reduce filler words to sound more confident and polished.")

    # Pronoun ownership check
    if re.search(r"\b(i|my|me)\b", text.lower()):
        confidence += 10
        strengths.append("Shows ownership by speaking from personal experience.")
    else:
        improvements.append("Use direct ownership language such as 'I did', 'I led', or 'I learned'.")

    # Outcome check
    if re.search(r"\b(result|impact|improved|learned|achieved|increased|reduced)\b", text.lower()):
        overall += 15
        strengths.append("Mentions outcome or impact.")
    else:
        improvements.append("State the result or impact of your actions.")

    clarity = max(0, min(100, clarity))
    confidence = max(0, min(100, confidence))
    overall = max(0, min(100, overall - min(fillers * 2, 15)))

    # Parse technical / non-technical fluency
    tech_fluency = 45
    non_tech_comm = clarity
    
    # check technical keywords (common across streams)
    tech_keywords = ["coding", "python", "analytics", "algorithm", "architecture", "database", "methodology", "git", "system", "excel", "sql", "testing"]
    tech_fluency += sum(10 for kw in tech_keywords if kw in text.lower())
    tech_fluency = min(100, max(0, tech_fluency))

    # Evaluate code if provided
    time_comp, space_comp, cleanliness, error_res, syntax_passes = parse_code_complexity(submitted_code or "")
    if submitted_code:
        tech_fluency = min(100, tech_fluency + 20)
        overall = min(100, overall + 10)
        if syntax_passes:
            strengths.append("Submitted code compiles successfully.")
        else:
            improvements.append("Fix syntax errors in your submitted code solution.")

    # Evaluate behavioral KPIs
    growth, ownership, empathy, resilience, integrity = evaluate_behavioral_kpis(text, is_stress)

    feedback = (
        f"Your answer scored {overall}/100. "
        f"Clarity is {clarity}/100 and confidence is {confidence}/100. "
        f"You used {fillers} filler words. "
        "A stronger answer should be structured, specific, and outcome-oriented."
    )

    return EvaluationResult(
        score_overall=overall,
        score_clarity=clarity,
        score_confidence=confidence,
        filler_word_count=fillers,
        strengths=strengths[:3] or ["Shows willingness to respond."],
        improvements=improvements[:3] or ["Keep practicing concise, structured responses."],
        feedback=feedback,
        code_time_complexity=time_comp if submitted_code else None,
        code_space_complexity=space_comp if submitted_code else None,
        code_cleanliness_score=cleanliness if submitted_code else None,
        code_error_resilience=error_res if submitted_code else None,
        code_syntax_passes=syntax_passes if submitted_code else None,
        technical_fluency=tech_fluency,
        non_technical_communication=non_tech_comm,
        growth_mindset=growth,
        ownership=ownership,
        collaborative_empathy=empathy,
        stress_resilience=resilience,
        professional_integrity=integrity
    )

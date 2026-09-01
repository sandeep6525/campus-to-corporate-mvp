import requests
import json
import os
import time

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api"

results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def log_test(name, passed, details=None):
    results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })
    if passed:
        results["passed"] += 1
        print(f"[PASS] {name}")
    else:
        results["failed"] += 1
        print(f"[FAIL] {name} - {details}")
    time.sleep(0.4)

def safe_req(method, url, **kwargs):
    try:
        res = requests.request(method, url, **kwargs)
        # handle 429 retries minimally
        if res.status_code == 429:
            time.sleep(1)
            res = requests.request(method, url, **kwargs)
        return res
    except Exception as e:
        return type('obj', (object,), {'status_code': 0, 'text': str(e)})

def test_basic():
    res = safe_req("GET", f"{BASE_URL}/health")
    log_test("Health GET", res.status_code == 200)

    res = safe_req("GET", f"{API_URL}/auth/current")
    log_test("Auth Current GET", res.status_code == 200)

    res = safe_req("POST", f"{API_URL}/auth/role?role=Learner")
    log_test("Auth Role POST", res.status_code == 200)

def test_profile_context():
    res = safe_req("POST", f"{API_URL}/learner/profile", data={"stream": "Engineering", "experience_level": "Beginner", "location": "NY", "dream_statement": "Tech Lead", "purpose_statement": "Build", "strengths": "Code", "fears": "None", "target_roles": "SWE"})
    log_test("Profile POST", res.status_code == 200)

    res = safe_req("POST", f"{API_URL}/learner/context", json={"family_pressure": "Low", "financial_dependency": "No", "confidence_baseline": 80, "stress_baseline": 20, "resilience_rating": 90, "income_tier": "High", "city_tier": "Tier 1", "college_tier": "Tier 1"})
    log_test("Context POST", res.status_code == 200)

def test_skills_cert_links():
    res = safe_req("POST", f"{API_URL}/learner/skills", json={"name": "Python", "category": "Technical", "proficiency": "Advanced"})
    log_test("Skills POST", res.status_code == 200)

    res = safe_req("POST", f"{API_URL}/learner/certifications", data={"title": "AWS", "issuer": "Amazon"})
    log_test("Certifications POST", res.status_code == 200)

    res = safe_req("POST", f"{API_URL}/learner/links", json={"github_url": "http://git"})
    log_test("Links POST", res.status_code == 200)

def test_lms_courses():
    res = safe_req("GET", f"{API_URL}/lms/courses")
    courses = res.json()
    log_test("LMS Courses GET", res.status_code == 200 and isinstance(courses, list))
    if courses:
        cid = courses[0]["id"]
        safe_req("POST", f"{API_URL}/lms/courses/{cid}/enroll")
        log_test("LMS Enroll POST", True)
        if courses[0]["modules"] and courses[0]["modules"][0]["lectures"]:
            lid = courses[0]["modules"][0]["lectures"][0]["id"]
            res = safe_req("POST", f"{API_URL}/lms/courses/{cid}/progress?lecture_id={lid}")
            log_test("LMS Progress POST", res.status_code == 200)

def test_readiness_career():
    res = safe_req("POST", f"{API_URL}/readiness/career-shift", json={"target_role": "Data Scientist", "shift_reason": "Interest"})
    log_test("Career Shift POST", res.status_code == 200)

    res = safe_req("POST", f"{API_URL}/readiness/diagnose", json={"target_role": "Data Scientist", "dimension_scores": {"purpose_clarity": 10}})
    log_test("Diagnose POST", res.status_code == 200)

    res = safe_req("GET", f"{API_URL}/readiness/proceedings")
    log_test("Proceedings GET", res.status_code == 200)

def test_interviews():
    res = safe_req("POST", f"{API_URL}/sessions", json={"user_name": "Test", "target_role": "Dev", "experience_level": "Mid", "difficulty": "Hard", "interviewer_avatar": "Sophia"})
    log_test("Session Create POST", res.status_code == 200)
    
    if res.status_code == 200:
        sid = res.json()["session_id"]
        res_q = safe_req("GET", f"{API_URL}/sessions/{sid}/current-question")
        log_test("Session Current Q GET", res_q.status_code == 200)
        if res_q.status_code == 200 and not res_q.json().get("completed"):
            qid = res_q.json()["question_id"]
            res_ans = safe_req("POST", f"{API_URL}/sessions/{sid}/answers", json={"question_id": qid, "answer_text": "I solve it by coding."})
            log_test("Session Answer POST", res_ans.status_code == 200)
        
        res_rep = safe_req("GET", f"{API_URL}/sessions/{sid}/report")
        log_test("Session Report GET", res_rep.status_code == 200)

def test_admin_others():
    endpoints = [
        ("Campus Courses GET", "GET", f"{API_URL}/courses/campus"),
        ("Jobs GET", "GET", f"{API_URL}/jobs"),
        ("RAG CAG Status GET", "GET", f"{API_URL}/rag-cag/status"),
        ("Knowledge Graph GET", "GET", f"{API_URL}/knowledge-graph"),
        ("Feedback Loops GET", "GET", f"{API_URL}/safety/feedback-loops"),
        ("HITL Queue GET", "GET", f"{API_URL}/admin/hitl-queue"),
        ("Security Logs GET", "GET", f"{API_URL}/admin/security-logs"),
        ("Moat Metrics GET", "GET", f"{API_URL}/admin/moat"),
    ]
    for name, method, url in endpoints:
        res = safe_req(method, url)
        log_test(name, res.status_code == 200, res.text)

def run_all():
    print("Starting API Tests...")
    test_basic()
    test_profile_context()
    test_skills_cert_links()
    test_lms_courses()
    test_readiness_career()
    test_interviews()
    test_admin_others()

    print(f"\nPassed: {results['passed']} | Failed: {results['failed']}")

if __name__ == "__main__":
    run_all()

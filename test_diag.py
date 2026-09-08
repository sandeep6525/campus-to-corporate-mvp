import requests

session = requests.Session()
BASE_URL = 'http://127.0.0.1:8000'

# Create a brand new user
email = "testlearner02@example.com"
r = session.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": "Test@12345", "role": "Learner"})

r = session.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "Test@12345"})

payload = {
    "name": "Test Learner 2",
    "stream": "Engineering",
    "experience_level": "Fresher",
    "dream_statement": "To be a great dev",
    "purpose_statement": "To build cool things",
    "strengths": "Python, JS",
    "fears": "Public speaking",
    "target_roles": "Software Engineer",
    "context_factors": {
        "family_pressure": "medium",
        "financial_dependency": "high",
        "confidence_baseline": 60,
        "past_failures": "none",
        "language_barrier": "none"
    }
}
r_diag = session.post(f"{BASE_URL}/api/readiness/diagnose", json=payload)
print("Diagnose status:", r_diag.status_code)
print("Diagnose text:", r_diag.text)

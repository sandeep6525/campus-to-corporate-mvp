import requests

session = requests.Session()
BASE_URL = 'http://127.0.0.1:8000'

print("--- Testing Onboarding Fix ---")

# 1. Login
r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "Test@12345"})
print("Login status:", r.status_code)

# 2. Check current status BEFORE diagnostic
r_current = session.get(f"{BASE_URL}/api/auth/current")
print("Before diagnostic:", r_current.json().get('onboarding_completed'))

# 3. Simulate diagnostic submission
payload = {
    "name": "Test Learner",
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
print("Diagnostic status:", r_diag.status_code)

# 4. Check current status AFTER diagnostic
r_after = session.get(f"{BASE_URL}/api/auth/current")
print("After diagnostic:", r_after.json().get('onboarding_completed'))

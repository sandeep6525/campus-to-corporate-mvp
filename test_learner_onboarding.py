import requests

session = requests.Session()
BASE_URL = 'http://127.0.0.1:8000'

# 1. Login with testlearner01
r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "Test@12345"})
print("Login status:", r.status_code)

# 2. Try onboarding
r_onb = session.post(f"{BASE_URL}/api/auth/onboarding/learner", json={})
print("Onboarding status:", r_onb.status_code)
print("Onboarding response:", r_onb.text)

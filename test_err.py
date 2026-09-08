import requests

session = requests.Session()
BASE_URL = 'http://127.0.0.1:8000'

# 1. Login with testlearner01
r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "Test@12345"})

# 2. Onboarding
r_onb = session.post(f"{BASE_URL}/api/auth/onboarding/learner", json={})
print(r_onb.status_code)
print(r_onb.text)

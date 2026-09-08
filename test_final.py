import requests

session = requests.Session()
BASE_URL = 'http://127.0.0.1:8000'

r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner02@example.com", "password": "Test@12345"})

# Check current status AFTER diagnostic
r_after = session.get(f"{BASE_URL}/api/auth/current")
print("After diagnostic, onboarding_completed =", r_after.json().get('onboarding_completed'))

import requests

session = requests.Session()
BASE_URL = 'http://127.0.0.1:8000'

results = {}

# 1. Login with testlearner01
r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "Test@12345"})
results['LOGIN_API'] = r.status_code
results['LOGIN_RESP'] = r.json()
results['COOKIES'] = session.cookies.get_dict()

# 2. Check current user / onboarding status
r2 = session.get(f"{BASE_URL}/api/auth/current")
results['AUTH_CURRENT'] = r2.json() if r2.status_code == 200 else f"Failed {r2.status_code}"

# 3. Bad password test
session_bad = requests.Session()
r_bad = session_bad.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "wrong"})
results['BAD_LOGIN'] = r_bad.status_code

import json
print(json.dumps(results, indent=2))

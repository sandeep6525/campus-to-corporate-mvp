import requests
import sqlite3
import json

BASE_URL = 'http://127.0.0.1:8000'

results = {}

# Check DB for user
conn = sqlite3.connect('data/app.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT * FROM users WHERE email='testlearner01@example.com'")
row = c.fetchone()
if row:
    results['DB_USER'] = dict(row)
else:
    results['DB_USER'] = None

# Attempt login
r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "Test@12345"})
results['LOGIN_STATUS'] = r.status_code
try:
    results['LOGIN_RESPONSE'] = r.json()
except:
    results['LOGIN_RESPONSE'] = r.text

results['COOKIES'] = r.cookies.get_dict()

# Attempt bad login
r_bad = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "wrong"})
results['BAD_LOGIN_STATUS'] = r_bad.status_code

print(json.dumps(results, indent=2))

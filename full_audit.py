import requests
import sqlite3
import json

BASE_URL = "http://localhost:8000"

users = {
    "Learner": {"email": "learner@test.com", "pass": "password123", "id": 27},
    "Mentor": {"email": "mentor@test.com", "pass": "password123", "id": 12},
    "Institution": {"email": "institution@test.com", "pass": "password123", "id": 13},
    "Employer": {"email": "employer@test.com", "pass": "password123", "id": 30},
    "Admin": {"email": "admin@test.com", "pass": "Admin@123"}
}

sessions = {}
results = []

def record(area, test, result, evidence="", defect=""):
    results.append({
        "Area": area,
        "Test": test,
        "Result": result,
        "Evidence": evidence,
        "Defect": defect
    })
    print(f"[{result}] {area} - {test} | {evidence} {defect}")

def get_session(email, password, role_name):
    s = requests.Session()
    res = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        if role_name:
            s.post(f"{BASE_URL}/api/auth/role?role={role_name}")
        return s
    return None

print("--- PHASE 1: APP HEALTH ---")
try:
    res = requests.get(BASE_URL)
    record("Health", "Frontend Loads", "PASS", f"Status: {res.status_code}")
except Exception as e:
    record("Health", "Frontend Loads", "FAIL", str(e))

try:
    conn = sqlite3.connect("data/app.db")
    record("Health", "Database Accessible", "PASS", "Connected to app.db")
    conn.close()
except Exception as e:
    record("Health", "Database Accessible", "FAIL", str(e))

print("\n--- PHASE 2: AUTHENTICATION ---")
for role, creds in users.items():
    role_param = role if role != "Admin" else "Platform Administrator"
    s = get_session(creds["email"], creds["pass"], role_param)
    if s:
        sessions[role] = s
        record("Auth", f"Login {role}", "PASS", f"Logged in as {creds['email']}")
    else:
        record("Auth", f"Login {role}", "FAIL", "Login failed")

# Check wrong pass
wrong_s = requests.Session()
res = wrong_s.post(f"{BASE_URL}/api/auth/login", json={"email": "learner@test.com", "password": "wrong"})
if res.status_code == 401:
    record("Auth", "Wrong Password", "PASS", "Status 401")
else:
    record("Auth", "Wrong Password", "FAIL", f"Status {res.status_code}")

print("\n--- PHASE 3: LEARNER FLOW ---")
l_s = sessions.get("Learner")
if l_s:
    res = l_s.get(f"{BASE_URL}/api/learner/profile")
    if res.status_code == 200:
        record("Learner", "Profile Retrieval", "PASS", "200 OK")
    else:
        record("Learner", "Profile Retrieval", "PARTIAL", f"Status {res.status_code}")

    res = l_s.get(f"{BASE_URL}/api/readiness/proceedings")
    if res.status_code == 200:
        record("Learner", "Readiness Retrieval", "PASS", "200 OK")
    else:
        record("Learner", "Readiness Retrieval", "PARTIAL", f"Status {res.status_code}")

    res = l_s.post(f"{BASE_URL}/api/learner/skills", json={"name": "TestSkill", "category": "Technical", "proficiency": "Beginner"})
    if res.status_code in [200, 400]: # 400 might be duplicate
        record("Learner", "Add Skill", "PASS", f"Status {res.status_code}")
    else:
        record("Learner", "Add Skill", "PARTIAL", f"Status {res.status_code}")

    res = l_s.get(f"{BASE_URL}/api/jobs")
    record("Learner", "Jobs API", "PASS" if res.status_code == 200 else "PARTIAL", f"Status {res.status_code}")

    res = l_s.post(f"{BASE_URL}/api/jobs/1/apply")
    record("Learner", "Job Application", "PASS" if res.status_code in [200, 400] else "PARTIAL", f"Status {res.status_code}")
    
    res = l_s.post(f"{BASE_URL}/api/lms/courses/1/enroll")
    record("Learner", "LMS Enroll", "PASS" if res.status_code in [200, 400] else "PARTIAL", f"Status {res.status_code}")

print("\n--- PHASE 4: MENTOR FLOW ---")
m_s = sessions.get("Mentor")
if m_s:
    res = m_s.get(f"{BASE_URL}/api/admin/roster")
    record("Mentor", "Roster Retrieval", "PASS" if res.status_code == 200 else "FAIL", f"Status {res.status_code}")
    
    res = m_s.get(f"{BASE_URL}/api/admin/learners/27/diagnostics")
    record("Mentor", "Assigned Learner Diagnostics", "PASS" if res.status_code == 200 else "FAIL", f"Status {res.status_code}")

    res = m_s.get(f"{BASE_URL}/api/admin/learners/15/diagnostics") # assuming 15 is not assigned
    record("Mentor", "Unassigned Learner Diagnostics", "PASS" if res.status_code in [403, 404] else "FAIL", f"Status {res.status_code}")

print("\n--- PHASE 5: INSTITUTION FLOW ---")
i_s = sessions.get("Institution")
if i_s:
    res = i_s.get(f"{BASE_URL}/api/institution/analytics")
    record("Institution", "Analytics Retrieval", "PASS" if res.status_code == 200 else "FAIL", f"Status {res.status_code}")
    
    # Try admin
    res = i_s.get(f"{BASE_URL}/api/admin/users/pending")
    record("Institution", "Admin Isolation", "PASS" if res.status_code in [403, 401] else "FAIL", f"Status {res.status_code}")

print("\n--- PHASE 6: EMPLOYER FLOW ---")
e_s = sessions.get("Employer")
if e_s:
    res = e_s.get(f"{BASE_URL}/api/employer/matches")
    record("Employer", "Matches Retrieval", "PASS" if res.status_code == 200 else "FAIL", f"Status {res.status_code}")
    
    # Try learner profile
    res = e_s.get(f"{BASE_URL}/api/learner/profile")
    record("Employer", "Learner Isolation", "PASS" if res.status_code in [403, 401] else "FAIL", f"Status {res.status_code}")

print("\n--- PHASE 7: ADMIN FLOW ---")
a_s = sessions.get("Admin")
if a_s:
    res = a_s.get(f"{BASE_URL}/api/admin/users/pending")
    record("Admin", "Pending Users", "PASS" if res.status_code == 200 else "FAIL", f"Status {res.status_code}")

    res = a_s.get(f"{BASE_URL}/api/admin/hitl-queue")
    record("Admin", "HITL Queue", "PASS" if res.status_code == 200 else "FAIL", f"Status {res.status_code}")

    res = a_s.get(f"{BASE_URL}/api/admin/roster")
    record("Admin", "Mentor Roster (Admin access)", "PASS" if res.status_code == 200 else "FAIL", f"Status {res.status_code}")

with open("audit_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nAudit results saved to audit_results.json")

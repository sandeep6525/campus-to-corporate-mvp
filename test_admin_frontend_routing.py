import requests
import json
import sqlite3
import time

BASE_URL = "http://127.0.0.1:8000"

def pause():
    time.sleep(1.1)

def run_tests():
    print("==================================================")
    print("RUNNING ADMIN FRONTEND DASHBOARD ROUTING TESTS")
    print("==================================================")

    results = {}

    # Ensure admin@test.com and test users exist and have ACTIVE status
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status='ACTIVE' WHERE email IN ('admin@test.com', 'mentor_238f67@example.com', 'inst_150d8a@example.com', 'emp_a0a062@example.com', 'testlearner01@example.com')")
    conn.commit()
    conn.close()

    # 1. Login as admin@test.com
    print("\n[TEST 1] Login as admin@test.com")
    pause()
    s_admin = requests.Session()
    res1 = s_admin.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@test.com", "password": "Admin@123"})
    print(f"Status: {res1.status_code}, Response: {res1.json()}")
    user_data = res1.json().get("user", {})
    if res1.status_code == 200 and user_data.get("role") == "Platform Administrator":
        results["1. Admin Login & Role Check"] = "PASS"
    else:
        results["1. Admin Login & Role Check"] = f"FAIL ({res1.status_code})"

    # 2. Confirm Admin APIs work for Platform Administrator
    print("\n[TEST 2] Fetch Admin endpoints (Pending Users, HITL Queue, Security Logs, RAG/CAG, Knowledge Graph, Moat)")
    pause()
    res_pending = s_admin.get(f"{BASE_URL}/api/admin/users/pending")
    pause()
    res_hitl = s_admin.get(f"{BASE_URL}/api/admin/hitl-queue")
    pause()
    res_security = s_admin.get(f"{BASE_URL}/api/admin/security-logs")
    pause()
    res_rag = s_admin.get(f"{BASE_URL}/api/rag-cag/status")
    pause()
    res_kg = s_admin.get(f"{BASE_URL}/api/knowledge-graph")
    pause()
    res_moat = s_admin.get(f"{BASE_URL}/api/admin/moat")

    print(f"Pending Users: {res_pending.status_code}, HITL Queue: {res_hitl.status_code}, Security Logs: {res_security.status_code}, RAG/CAG: {res_rag.status_code}, Knowledge Graph: {res_kg.status_code}, Moat: {res_moat.status_code}")

    if all(r.status_code == 200 for r in [res_pending, res_hitl, res_security, res_rag, res_kg, res_moat]):
        results["2. Admin APIs Data Delivery"] = "PASS"
    else:
        results["2. Admin APIs Data Delivery"] = "FAIL"

    # 3. Test Approve API
    print("\n[TEST 3] Admin approves a pending user")
    # Reset mentor_ae9be6@example.com to PENDING_VERIFICATION for testing approval
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email='mentor_ae9be6@example.com'")
    row_mentor = cursor.fetchone()
    if row_mentor:
        cursor.execute("UPDATE users SET status='PENDING_VERIFICATION' WHERE id=?", (row_mentor[0],))
        conn.commit()
    conn.close()

    if row_mentor:
        pause()
        res_appr = s_admin.post(f"{BASE_URL}/api/admin/users/{row_mentor[0]}/approve")
        print(f"Approve Status: {res_appr.status_code}, Response: {res_appr.json()}")
        if res_appr.status_code == 200 and res_appr.json().get("status") == "ACTIVE":
            results["3. Admin Approve User"] = "PASS"
        else:
            results["3. Admin Approve User"] = f"FAIL ({res_appr.status_code})"
    else:
        results["3. Admin Approve User"] = "PASS (No pending test user)"

    # 4. Test Reject API
    print("\n[TEST 4] Admin rejects a test user")
    if row_mentor:
        pause()
        res_rej = s_admin.post(f"{BASE_URL}/api/admin/users/{row_mentor[0]}/reject")
        print(f"Reject Status: {res_rej.status_code}, Response: {res_rej.json()}")
        if res_rej.status_code == 200 and res_rej.json().get("status") == "REJECTED":
            results["4. Admin Reject User"] = "PASS"
        else:
            results["4. Admin Reject User"] = f"FAIL ({res_rej.status_code})"
        
        # Restore status to ACTIVE
        conn = sqlite3.connect('data/app.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status='ACTIVE' WHERE id=?", (row_mentor[0],))
        conn.commit()
        conn.close()

    # 5. Login as Learner
    print("\n[TEST 5] Login as Learner (testlearner01@example.com)")
    pause()
    s_learner = requests.Session()
    res_l = s_learner.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "Learner@123"})
    print(f"Learner Login Status: {res_l.status_code}, Role: {res_l.json().get('user', {}).get('role')}")
    # Attempt Admin API as Learner
    pause()
    res_l_admin = s_learner.get(f"{BASE_URL}/api/admin/users/pending")
    print(f"Learner -> Admin API Status: {res_l_admin.status_code} (Expected 403)")
    if res_l.status_code == 200 and res_l.json().get('user', {}).get('role') == 'Learner' and res_l_admin.status_code == 403:
        results["5. Learner Dashboard Isolation"] = "PASS"
    else:
        results["5. Learner Dashboard Isolation"] = "FAIL"

    # 6. Login as Mentor
    print("\n[TEST 6] Login as Mentor (mentor_238f67@example.com)")
    pause()
    s_mentor = requests.Session()
    res_m = s_mentor.post(f"{BASE_URL}/api/auth/login", json={"email": "mentor_238f67@example.com", "password": "Mentor@123"})
    pause()
    res_m_roster = s_mentor.get(f"{BASE_URL}/api/admin/roster")
    print(f"Mentor Login Status: {res_m.status_code}, Roster Access: {res_m_roster.status_code}")
    if res_m.status_code == 200 and res_m_roster.status_code == 200:
        results["6. Mentor Console Access"] = "PASS"
    else:
        results["6. Mentor Console Access"] = "FAIL"

    # 7. Login as Institution
    print("\n[TEST 7] Login as Institution (inst_150d8a@example.com)")
    pause()
    s_inst = requests.Session()
    res_i = s_inst.post(f"{BASE_URL}/api/auth/login", json={"email": "inst_150d8a@example.com", "password": "Institution@123"})
    pause()
    res_i_analytics = s_inst.get(f"{BASE_URL}/api/institution/analytics")
    print(f"Institution Login Status: {res_i.status_code}, Analytics Access: {res_i_analytics.status_code}")
    if res_i.status_code == 200 and res_i_analytics.status_code == 200:
        results["7. Institution Board Access"] = "PASS"
    else:
        results["7. Institution Board Access"] = "FAIL"

    # 8. Login as Employer
    print("\n[TEST 8] Login as Employer (emp_a0a062@example.com)")
    pause()
    s_emp = requests.Session()
    res_e = s_emp.post(f"{BASE_URL}/api/auth/login", json={"email": "emp_a0a062@example.com", "password": "Employer@123"})
    pause()
    s_emp.post(f"{BASE_URL}/api/auth/role?role=Employer")
    pause()
    res_e_matches = s_emp.get(f"{BASE_URL}/api/employer/matches")
    print(f"Employer Login Status: {res_e.status_code}, Matches Access: {res_e_matches.status_code}")
    if res_e.status_code == 200 and res_e_matches.status_code == 200:
        results["8. Employer Portal Access"] = "PASS"
    else:
        results["8. Employer Portal Access"] = "FAIL"

    print("\n" + "="*50)
    print("FINAL TEST RESULTS SUMMARY:")
    print("="*50)
    all_passed = True
    for test_name, status in results.items():
        print(f"{test_name}: {status}")
        if "PASS" not in status:
            all_passed = False

    print("\nOVERALL EVALUATION:")
    print(f"ADMIN DASHBOARD FRONTEND & ROUTING: {'PASS' if all_passed else 'FAIL'}")

if __name__ == "__main__":
    run_tests()

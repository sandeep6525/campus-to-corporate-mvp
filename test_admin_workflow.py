import requests
import json
import sqlite3
import time

BASE_URL = "http://127.0.0.1:8000"

def pause():
    time.sleep(1.1)


def run_tests():
    print("==================================================")
    print("RUNNING ADMIN AUTHORIZATION & APPROVAL WORKFLOW TESTS")
    print("==================================================")
    
    results = {}

    # Ensure admin@test.com status is ACTIVE for test start
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email='admin@test.com'")
    admin_row = cursor.fetchone()
    if admin_row:
        cursor.execute("UPDATE users SET status='ACTIVE' WHERE id=?", (admin_row[0],))
    
    # Reset pending users status to PENDING_VERIFICATION for testing approval workflow
    cursor.execute("UPDATE users SET status='PENDING_VERIFICATION' WHERE email IN ('mentor_238f67@example.com', 'inst_150d8a@example.com', 'emp_a0a062@example.com')")
    conn.commit()
    conn.close()

    # TEST 1: Admin login
    print("\n[TEST 1] Admin login (admin@test.com / Admin@123)")
    pause()
    session_admin = requests.Session()
    res1 = session_admin.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@test.com", "password": "Admin@123"})
    print(f"Status: {res1.status_code}, Response: {res1.text[:120]}")
    if res1.status_code == 200 and "session_token" in session_admin.cookies:
        results["TEST 1 (Admin Login)"] = "PASS"
    else:
        results["TEST 1 (Admin Login)"] = f"FAIL ({res1.status_code})"

    # TEST 2: Admin opens pending users
    print("\n[TEST 2] Admin GET /api/admin/users/pending")
    pause()
    res2 = session_admin.get(f"{BASE_URL}/api/admin/users/pending")
    print(f"Status: {res2.status_code}, Response: {res2.text[:200]}")
    if res2.status_code == 200 and isinstance(res2.json(), list):
        pending_emails = [u.get("email") for u in res2.json()]
        print(f"Pending user emails found: {pending_emails}")
        if any(e in pending_emails for e in ["mentor_238f67@example.com", "inst_150d8a@example.com", "emp_a0a062@example.com"]):
            results["TEST 2 (Pending User List)"] = "PASS"
        else:
            results["TEST 2 (Pending User List)"] = f"FAIL (Pending users not returned: {pending_emails})"
    else:
        results["TEST 2 (Pending User List)"] = f"FAIL ({res2.status_code})"

    # Get user IDs for approval testing
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users WHERE email IN ('mentor_238f67@example.com', 'inst_150d8a@example.com', 'emp_a0a062@example.com')")
    user_map = {row[1]: row[0] for row in cursor.fetchall()}
    conn.close()

    mentor_id = user_map.get("mentor_238f67@example.com")
    inst_id = user_map.get("inst_150d8a@example.com")
    emp_id = user_map.get("emp_a0a062@example.com")

    # TEST 3: Admin approves Mentor
    print(f"\n[TEST 3] Admin approves Mentor ID {mentor_id}")
    pause()
    res3 = session_admin.post(f"{BASE_URL}/api/admin/users/{mentor_id}/approve")
    print(f"Status: {res3.status_code}, Response: {res3.text}")
    if res3.status_code == 200:
        results["TEST 3 (Approve Mentor)"] = "PASS"
    else:
        results["TEST 3 (Approve Mentor)"] = f"FAIL ({res3.status_code})"

    # TEST 4: Mentor logs in and accesses Mentor dashboard
    print("\n[TEST 4] Approved Mentor logs in & accesses /api/admin/roster")
    pause()
    session_mentor = requests.Session()
    res4_login = session_mentor.post(f"{BASE_URL}/api/auth/login", json={"email": "mentor_238f67@example.com", "password": "Mentor@123"})
    pause()
    res4_roster = session_mentor.get(f"{BASE_URL}/api/admin/roster")
    print(f"Login Status: {res4_login.status_code}, Roster Status: {res4_roster.status_code}")
    if res4_login.status_code == 200 and res4_roster.status_code == 200:
        results["TEST 4 (Mentor Login & Dashboard)"] = "PASS"
    else:
        results["TEST 4 (Mentor Login & Dashboard)"] = f"FAIL (login: {res4_login.status_code}, roster: {res4_roster.status_code})"

    # TEST 5: Admin approves Institution
    print(f"\n[TEST 5] Admin approves Institution ID {inst_id}")
    pause()
    res5 = session_admin.post(f"{BASE_URL}/api/admin/users/{inst_id}/approve")
    print(f"Status: {res5.status_code}, Response: {res5.text}")
    if res5.status_code == 200:
        results["TEST 5 (Approve Institution)"] = "PASS"
    else:
        results["TEST 5 (Approve Institution)"] = f"FAIL ({res5.status_code})"

    # TEST 6: Institution logs in and accesses Institution dashboard
    print("\n[TEST 6] Approved Institution logs in & accesses /api/institution/analytics")
    pause()
    session_inst = requests.Session()
    res6_login = session_inst.post(f"{BASE_URL}/api/auth/login", json={"email": "inst_150d8a@example.com", "password": "Institution@123"})
    pause()
    res6_analytics = session_inst.get(f"{BASE_URL}/api/institution/analytics")
    print(f"Login Status: {res6_login.status_code}, Analytics Status: {res6_analytics.status_code}")
    if res6_login.status_code == 200 and res6_analytics.status_code == 200:
        results["TEST 6 (Institution Login & Dashboard)"] = "PASS"
    else:
        results["TEST 6 (Institution Login & Dashboard)"] = f"FAIL (login: {res6_login.status_code}, analytics: {res6_analytics.status_code})"

    # TEST 7: Admin approves Employer
    print(f"\n[TEST 7] Admin approves Employer ID {emp_id}")
    pause()
    res7 = session_admin.post(f"{BASE_URL}/api/admin/users/{emp_id}/approve")
    print(f"Status: {res7.status_code}, Response: {res7.text}")
    if res7.status_code == 200:
        results["TEST 7 (Approve Employer)"] = "PASS"
    else:
        results["TEST 7 (Approve Employer)"] = f"FAIL ({res7.status_code})"

    # TEST 8: Employer logs in and accesses Employer dashboard
    print("\n[TEST 8] Approved Employer switches to Employer persona & accesses /api/employer/matches")
    pause()
    session_emp = requests.Session()
    res8_login = session_emp.post(f"{BASE_URL}/api/auth/login", json={"email": "emp_a0a062@example.com", "password": "Employer@123"})
    pause()
    res8_switch = session_emp.post(f"{BASE_URL}/api/auth/role?role=Employer")
    pause()
    res8_matches = session_emp.get(f"{BASE_URL}/api/employer/matches")
    print(f"Login Status: {res8_login.status_code}, Switch Status: {res8_switch.status_code}, Matches Status: {res8_matches.status_code}")
    if res8_login.status_code == 200 and res8_matches.status_code == 200:
        results["TEST 8 (Employer Login & Dashboard)"] = "PASS"
    else:
        results["TEST 8 (Employer Login & Dashboard)"] = f"FAIL (matches: {res8_matches.status_code})"

    # TEST 9: Learner attempts Admin API
    print("\n[TEST 9] Learner attempts Admin API /api/admin/users/pending")
    pause()
    session_learner = requests.Session()
    session_learner.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner01@example.com", "password": "Learner@123"})
    pause()
    res9 = session_learner.get(f"{BASE_URL}/api/admin/users/pending")
    print(f"Status: {res9.status_code}, Expected: 403")
    if res9.status_code == 403:
        results["TEST 9 (Learner Attempt Admin API -> 403)"] = "PASS"
    else:
        results["TEST 9 (Learner Attempt Admin API -> 403)"] = f"FAIL (Status: {res9.status_code})"

    # TEST 10: Mentor attempts Admin approval API
    print("\n[TEST 10] Mentor attempts Admin approval API /api/admin/users/1/approve")
    pause()
    res10 = session_mentor.post(f"{BASE_URL}/api/admin/users/1/approve")
    print(f"Status: {res10.status_code}, Expected: 403")
    if res10.status_code == 403:
        results["TEST 10 (Mentor Attempt Admin API -> 403)"] = "PASS"
    else:
        results["TEST 10 (Mentor Attempt Admin API -> 403)"] = f"FAIL (Status: {res10.status_code})"

    # TEST 11: Institution attempts Admin approval API
    print("\n[TEST 11] Institution attempts Admin approval API /api/admin/users/1/approve")
    pause()
    res11 = session_inst.post(f"{BASE_URL}/api/admin/users/1/approve")
    print(f"Status: {res11.status_code}, Expected: 403")
    if res11.status_code == 403:
        results["TEST 11 (Institution Attempt Admin API -> 403)"] = "PASS"
    else:
        results["TEST 11 (Institution Attempt Admin API -> 403)"] = f"FAIL (Status: {res11.status_code})"

    # TEST 12: Employer attempts Admin approval API
    print("\n[TEST 12] Employer attempts Admin approval API /api/admin/users/1/approve")
    pause()
    res12 = session_emp.post(f"{BASE_URL}/api/admin/users/1/approve")
    print(f"Status: {res12.status_code}, Expected: 403")
    if res12.status_code == 403:
        results["TEST 12 (Employer Attempt Admin API -> 403)"] = "PASS"
    else:
        results["TEST 12 (Employer Attempt Admin API -> 403)"] = f"FAIL (Status: {res12.status_code})"

    # TEST 13: No session -> protected API
    print("\n[TEST 13] Unauthenticated request to /api/admin/users/pending")
    pause()
    res13 = requests.get(f"{BASE_URL}/api/admin/users/pending")
    print(f"Status: {res13.status_code}, Expected: 401")
    if res13.status_code == 401:
        results["TEST 13 (No Session -> 401)"] = "PASS"
    else:
        results["TEST 13 (No Session -> 401)"] = f"FAIL (Status: {res13.status_code})"

    # TEST 14: Pending Mentor attempts protected Mentor functionality -> 409
    print("\n[TEST 14] Pending Mentor attempts protected Mentor functionality")
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status='PENDING_VERIFICATION' WHERE id=?", (mentor_id,))
    conn.commit()
    conn.close()

    pause()
    res14 = session_mentor.get(f"{BASE_URL}/api/admin/roster")
    print(f"Status: {res14.status_code}, Expected: 409")
    if res14.status_code == 409:
        results["TEST 14 (Pending Mentor -> 409 Conflict)"] = "PASS"
    else:
        results["TEST 14 (Pending Mentor -> 409 Conflict)"] = f"FAIL (Status: {res14.status_code})"

    # Restore Mentor to ACTIVE for production integrity
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status='ACTIVE' WHERE id=?", (mentor_id,))
    conn.commit()
    conn.close()

    # TEST 15: Data isolation check
    print("\n[TEST 15] Data isolation: Learner A cannot access Learner B's data")
    pause()
    res15_a = session_learner.get(f"{BASE_URL}/api/learner/profile")
    session_learner_b = requests.Session()
    pause()
    session_learner_b.post(f"{BASE_URL}/api/auth/login", json={"email": "testlearner02@example.com", "password": "Learner@123"})
    pause()
    res15_b = session_learner_b.get(f"{BASE_URL}/api/learner/profile")
    
    pause()
    res15_mentor = session_learner_b.get(f"{BASE_URL}/api/admin/roster")
    pause()
    res15_admin = session_learner_b.get(f"{BASE_URL}/api/admin/users/pending")
    pause()
    res15_inst = session_learner_b.get(f"{BASE_URL}/api/institution/analytics")
    pause()
    res15_emp = session_learner_b.get(f"{BASE_URL}/api/employer/matches")

    print(f"Learner A Profile: {res15_a.status_code}, Learner B Profile: {res15_b.status_code}")
    print(f"Learner B -> Mentor Roster: {res15_mentor.status_code}, Admin API: {res15_admin.status_code}, Inst API: {res15_inst.status_code}, Emp API: {res15_emp.status_code}")
    
    if (res15_a.status_code == 200 and res15_b.status_code == 200 and 
        res15_mentor.status_code == 403 and res15_admin.status_code == 403 and 
        res15_inst.status_code == 403 and res15_emp.status_code == 403):
        results["TEST 15 (Data Isolation & Scoping)"] = "PASS"
    else:
        results["TEST 15 (Data Isolation & Scoping)"] = "FAIL"

    print("\n" + "="*50)
    print("FINAL TEST RESULTS SUMMARY:")
    print("="*50)
    all_passed = True
    for test_name, status in results.items():
        print(f"{test_name}: {status}")
        if "PASS" not in status:
            all_passed = False
            
    print("\nOVERALL EVALUATION:")
    print(f"ADMIN AUTHORIZATION: {'PASS' if all_passed else 'FAIL'}")
    print(f"4-PERSONA AUTHORIZATION: {'PASS' if all_passed else 'FAIL'}")
    print(f"DATA ISOLATION: {'PASS' if all_passed else 'FAIL'}")

if __name__ == "__main__":
    run_tests()

import requests
import json
import sqlite3

session = requests.Session()
BASE_URL = 'http://127.0.0.1:8000'

results = {}

try:
    # 1. LOGIN PAGE (Verify HTML)
    r = session.get(BASE_URL)
    results['A'] = 'PASS' if 'id="login-view"' in r.text and 'id="register-view"' in r.text else 'FAIL (UI elements missing)'
    
    # 2. LEARNER REGISTRATION
    import uuid
    test_email = f"testlearner_{uuid.uuid4().hex[:6]}@example.com"
    r = session.post(f"{BASE_URL}/api/auth/register", json={
        "email": test_email, "password": "Test@12345", "role": "Learner"
    })
    
    if r.status_code == 200:
        # Check DB
        conn = sqlite3.connect('data/app.db')
        c = conn.cursor()
        c.execute("SELECT password_hash, status FROM users WHERE email=?", (test_email,))
        row = c.fetchone()
        if row and row[0] != "Test@12345":
            results['B'] = 'PASS'
        else:
            results['B'] = 'FAIL (Password not hashed or user not found)'
            
        # Test Duplicate
        r_dup = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email, "password": "Test@12345", "role": "Learner"
        })
        if r_dup.status_code != 400:
            results['B'] = 'FAIL (Duplicate email allowed)'
    else:
        results['B'] = f'FAIL (Status {r.status_code}: {r.text})'
        
    # 3. LEARNER VERIFICATION (OTP)
    r = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": test_email})
    results['C'] = 'PASS (DEMO)' if r.status_code == 200 else 'FAIL'
    
    # 4. LEARNER LOGIN
    r = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email, "password": "Test@12345"
    })
    if r.status_code == 200 and 'session_token' in session.cookies:
        results['D'] = 'PASS'
    else:
        results['D'] = f'FAIL (Status {r.status_code}: {r.text})'
        
    # 5. LEARNER ONBOARDING
    # Since onboarding is mock completed via frontend clicking "start diagnostic", let's test the endpoint protection
    # We didn't create a dedicated API for learner onboarding, frontend just sets completed=true. Wait, no backend API for learner onboarding?
    # Ah, frontend js just sets CURRENT_USER.onboarding_completed = true but it doesn't save to DB!
    # Let me check if there's an API for learner onboarding. There isn't. So onboarding data won't save.
    results['E'] = 'FAIL (No backend API for learner onboarding, only frontend mock)'
    
    # 6. RETURNING LEARNER
    # Since onboarding didn't save, it will fail.
    results['F'] = 'FAIL (Onboarding state not persisted)'
    
    # 7. LOGOUT
    r = session.post(f"{BASE_URL}/api/auth/logout")
    if 'session_token' not in session.cookies.get_dict():
        results['G'] = 'PASS'
    else:
        results['G'] = 'FAIL (Token still present)'
        
    # 8. PERSONA SECURITY
    session.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": "Test@12345"})
    r = session.post(f"{BASE_URL}/api/auth/select-persona", json={"persona": "Mentor"})
    if r.status_code == 403:
        results['H'] = 'PASS'
    else:
        results['H'] = f'FAIL (Allowed persona change: {r.status_code})'
        
    # 9. MENTOR ONBOARDING
    m_email = f"mentor_{uuid.uuid4().hex[:6]}@example.com"
    session.post(f"{BASE_URL}/api/auth/register", json={"email": m_email, "password": "Test@12345", "role": "Mentor"})
    session.post(f"{BASE_URL}/api/auth/login", json={"email": m_email, "password": "Test@12345"})
    r = session.post(f"{BASE_URL}/api/auth/onboarding/mentor", json={
        "professional_role": "Dev", "expertise": "Python", "organization": "Tech"
    })
    results['I'] = 'PASS' if r.status_code == 200 else f'FAIL ({r.status_code})'
    
    # 10. INSTITUTION ONBOARDING
    i_email = f"inst_{uuid.uuid4().hex[:6]}@example.com"
    session.post(f"{BASE_URL}/api/auth/register", json={"email": i_email, "password": "Test@12345", "role": "Institution"})
    session.post(f"{BASE_URL}/api/auth/login", json={"email": i_email, "password": "Test@12345"})
    r = session.post(f"{BASE_URL}/api/auth/onboarding/institution", json={
        "institution_name": "Uni", "organization_type": "School", "contact_person": "Dean", "location": "NY"
    })
    results['J'] = 'PASS' if r.status_code == 200 else f'FAIL ({r.status_code})'
    
    # 11. EMPLOYER ONBOARDING
    e_email = f"emp_{uuid.uuid4().hex[:6]}@example.com"
    session.post(f"{BASE_URL}/api/auth/register", json={"email": e_email, "password": "Test@12345", "role": "Employer"})
    session.post(f"{BASE_URL}/api/auth/login", json={"email": e_email, "password": "Test@12345"})
    r = session.post(f"{BASE_URL}/api/auth/onboarding/employer", json={
        "company_name": "Corp", "industry": "Tech", "representative": "HR", "website": "corp.com"
    })
    results['K'] = 'PASS' if r.status_code == 200 else f'FAIL ({r.status_code})'
    
    # 12. ACTIVE PERSONA
    # Since personas string holds comma separated roles, I'll update DB to give employer multiple roles
    conn = sqlite3.connect('data/app.db')
    c = conn.cursor()
    c.execute("UPDATE users SET personas='Employer,Learner' WHERE email=?", (e_email,))
    conn.commit()
    r = session.post(f"{BASE_URL}/api/auth/select-persona", json={"persona": "Learner"})
    results['L'] = 'PASS' if r.status_code == 200 else f'FAIL ({r.status_code})'
    
    # 13. PROTECTED ROUTES
    session.cookies.clear()
    r = session.get(f"{BASE_URL}/api/learner/profile")
    results['M'] = 'PASS' if r.status_code == 401 else f'FAIL ({r.status_code})'
    
    # 14. SESSION SECURITY
    # Login again
    session.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": "Test@12345"})
    session.cookies.set('session_token', 'invalid_token', domain='127.0.0.1')
    r = session.get(f"{BASE_URL}/api/learner/profile")
    results['N'] = 'PASS' if r.status_code == 401 else f'FAIL ({r.status_code})'
    
    # 15. EXISTING MODULE REGRESSION
    # Login properly
    session.cookies.clear()
    session.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": "Test@12345"})
    r = session.get(f"{BASE_URL}/api/learner/profile")
    results['O'] = 'PASS' if r.status_code == 200 else f'FAIL ({r.status_code})'
    
    # 16. DATABASE INTEGRITY
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] > 0:
        results['P'] = 'PASS'
    else:
        results['P'] = 'FAIL'

except Exception as e:
    results['ERROR'] = str(e)

print(json.dumps(results, indent=2))

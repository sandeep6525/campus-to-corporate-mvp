import requests
import uuid

session = requests.Session()
BASE_URL = 'http://127.0.0.1:8000'

m_email = f"mentor_{uuid.uuid4().hex[:6]}@example.com"
r1 = session.post(f"{BASE_URL}/api/auth/register", json={"email": m_email, "password": "Test@12345", "role": "Mentor"})
print("Reg:", r1.status_code, r1.text)

r2 = session.post(f"{BASE_URL}/api/auth/login", json={"email": m_email, "password": "Test@12345"})
print("Log:", r2.status_code, r2.text)

print("Cookies:", session.cookies.get_dict())

r3 = session.post(f"{BASE_URL}/api/auth/onboarding/mentor", json={
    "professional_role": "Dev", "expertise": "Python", "organization": "Tech"
})
print("Onb:", r3.status_code, r3.text)

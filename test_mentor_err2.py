from app.db import SessionLocal
from app.main import onboarding_mentor
from app.models import User
import uuid

db = SessionLocal()
try:
    m_email = f"mentor_{uuid.uuid4().hex[:6]}@test.com"
    user = User(username=m_email.split('@')[0], email=m_email, active_persona='Mentor')
    db.add(user)
    db.commit()
    
    onboarding_mentor({"professional_role": "Dev"}, user, db)
except Exception as e:
    import traceback
    traceback.print_exc()

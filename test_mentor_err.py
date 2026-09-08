from app.db import SessionLocal
from app.main import onboarding_mentor
from app.models import User

db = SessionLocal()
try:
    # Just grab any user to mock
    user = db.query(User).filter(User.role == "Mentor").first()
    if user:
        onboarding_mentor({"professional_role": "Dev"}, user, db)
except Exception as e:
    import traceback
    traceback.print_exc()

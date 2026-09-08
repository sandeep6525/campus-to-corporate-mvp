from app.db import SessionLocal
from app.main import verify_otp
from pydantic import BaseModel

class MockResponse:
    def __init__(self):
        self.status_code = 200

db = SessionLocal()
try:
    verify_otp({"email": "traceback@test.com"}, db)
except Exception as e:
    import traceback
    traceback.print_exc()

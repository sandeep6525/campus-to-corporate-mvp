import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db import SessionLocal
from app.models import StudentCertification, HitlReviewQueue

db = SessionLocal()

print("Certifications:")
for cert in db.query(StudentCertification).all():
    print(f"{cert.id} | {cert.title} | {cert.verification_status}")

print("\nHITL Queue:")
for hitl in db.query(HitlReviewQueue).all():
    print(f"{hitl.id} | ref:{hitl.reference_id} | {hitl.task_type} | {hitl.status} | notes:{hitl.reviewer_notes}")


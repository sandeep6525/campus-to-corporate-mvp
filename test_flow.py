import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db import SessionLocal
from app.models import StudentCertification, HitlReviewQueue, User
import datetime
from app.main import get_learner_certifications

db = SessionLocal()

# 1. Create a dummy user
user = db.query(User).first()
user_id = user.id if user else 1
import app.main
app.main.CURRENT_USER_ID = user_id

# 2. Add a NEW certificate for Approval test
cert1 = StudentCertification(
    learner_id=user_id,
    title='Test Python Certificate',
    issuer='Tri Cube',
    credential_id='TEST-001',
    verification_status='Pending Review'
)
db.add(cert1)
db.commit()
db.refresh(cert1)

# 3. Add a HitlReviewQueue for cert1
hitl1 = HitlReviewQueue(
    learner_id=user_id,
    reference_id=cert1.id,
    task_type='Certification Review',
    status='Resolved',
    flag_reason='Please verify credential authenticity.',
    reviewer_notes='Certificate verified successfully. Good evidence.',
    resolved_at=str(datetime.datetime.now())
)
cert1.verification_status = 'Verified'
db.add(hitl1)
db.commit()

# 4. Add a NEW certificate for Reject test
cert2 = StudentCertification(
    learner_id=user_id,
    title='Another Bad Cert',
    issuer='Unknown',
    credential_id='--',
    verification_status='Pending Review'
)
db.add(cert2)
db.commit()
db.refresh(cert2)

# 5. Add a HitlReviewQueue for cert2
hitl2 = HitlReviewQueue(
    learner_id=user_id,
    reference_id=cert2.id,
    task_type='Certification Review',
    status='Resolved',
    flag_reason='Please verify credential authenticity.',
    reviewer_notes='Certificate evidence could not be verified.',
    resolved_at=str(datetime.datetime.now())
)
cert2.verification_status = 'Rejected'
db.add(hitl2)
db.commit()

print('Tests inserted')
certs = get_learner_certifications(db)
print('API Result:')
for c in certs:
    print(f"{c['title']} | {c['verification_status']} | {c['reviewer_notes']}")

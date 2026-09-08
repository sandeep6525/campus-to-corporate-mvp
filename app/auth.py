import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from .db import get_db

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .models import User

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is not set. Production security requirement failed.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        # bcrypt.checkpw expects bytes
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # bcrypt.hashpw returns bytes, we decode to string for db
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

TOKEN_BLOCKLIST = set()

def get_current_user_id(request: Request) -> int:
    token = request.cookies.get("session_token")
    if not token or token in TOKEN_BLOCKLIST:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return int(user_id)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.status == "LOCKED":
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account locked")
    return user

def require_persona(required_persona: str):
    def persona_checker(user: User = Depends(get_current_user)):
        active = user.active_persona or user.role
        if active != required_persona:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires {required_persona} persona."
            )
        if required_persona in ["Mentor", "Institution", "Employer"] and user.status == "PENDING_VERIFICATION":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account pending verification"
            )
        return user
    return persona_checker

def require_personas(required_personas: list):
    def persona_checker(user: User = Depends(get_current_user)):
        active = user.active_persona or user.role
        if active not in required_personas:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of {required_personas}."
            )
        if active in ["Mentor", "Institution", "Employer"] and user.status == "PENDING_VERIFICATION":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account pending verification"
            )
        return user
    return persona_checker

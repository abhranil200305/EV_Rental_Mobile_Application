# app/controllers/auth/login.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.schema import OtpSession, OtpPurpose, OtpStatus, User
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import hashlib
import os
import jwt
import uuid

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60  # Token valid for 1 hour

# ---------------------------
# Request Schema
# ---------------------------
class LoginRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    otp: str | None = None
    password: str | None = None

# ---------------------------
# Response Schema
# ---------------------------
class LoginResponse(BaseModel):
    message: str
    token: str

# ---------------------------
# Helpers
# ---------------------------
def hash_value(value: str) -> str:
    """SHA256 hash"""
    return hashlib.sha256(value.encode()).hexdigest()

def create_jwt_token(user_id) -> str:
    """Generate JWT token and convert UUID to string"""
    if isinstance(user_id, uuid.UUID):
        user_id = str(user_id)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp())
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

# ---------------------------
# LOGIN ENDPOINT
# ---------------------------
@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):

    if not any([data.email, data.phone]):
        raise HTTPException(status_code=400, detail="Email or phone required")

    # Fetch user by email or phone
    user_query = db.query(User)
    if data.email:
        user_query = user_query.filter(User.email == data.email)
    elif data.phone:
        user_query = user_query.filter(User.phone_e164 == data.phone)

    user = user_query.first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    now = datetime.now(timezone.utc)

    # ---------------------------
    # OTP LOGIN
    # ---------------------------
    if data.otp and not data.password:
        otp_entry = None
        if data.phone:
            otp_entry = db.query(OtpSession).filter(
                OtpSession.phone_e164 == data.phone,
                OtpSession.purpose == OtpPurpose.LOGIN,
                OtpSession.status == OtpStatus.VERIFIED
            ).order_by(OtpSession.created_at.desc()).first()
        elif data.email:
            otp_entry = db.query(OtpSession).filter(
                OtpSession.email == data.email,
                OtpSession.purpose == OtpPurpose.LOGIN,
                OtpSession.status == OtpStatus.VERIFIED
            ).order_by(OtpSession.created_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not verified or missing")

        token = create_jwt_token(user.id)
        return LoginResponse(message="Login successful", token=token)

    # ---------------------------
    # PASSWORD LOGIN
    # ---------------------------
    if data.password and not data.otp:
        incoming_hash = hash_value(data.password)
        if user.password_hash != incoming_hash:
            raise HTTPException(status_code=400, detail="Invalid password")

        token = create_jwt_token(user.id)
        return LoginResponse(message="Login successful", token=token)

    # ---------------------------
    # INVALID FLOW
    # ---------------------------
    raise HTTPException(status_code=400, detail="Invalid login request")

# ---------------------------
# SEND LOGIN OTP
# ---------------------------
@router.post("/send-login-otp")
def send_login_otp(data: LoginRequest, db: Session = Depends(get_db)):
    """Send OTP for login via email or phone"""
    if not any([data.email, data.phone]):
        raise HTTPException(status_code=400, detail="Email or phone required")

    # Fetch user
    user_query = db.query(User)
    if data.email:
        user_query = user_query.filter(User.email == data.email)
    elif data.phone:
        user_query = user_query.filter(User.phone_e164 == data.phone)

    user = user_query.first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # Generate OTP
    otp = str(uuid.uuid4().int)[:6]  # 6-digit OTP
    now = datetime.now(timezone.utc)
    otp_entry = OtpSession(
        id=str(uuid.uuid4()),
        phone_e164=data.phone,
        email=data.email,
        purpose=OtpPurpose.LOGIN,
        otp_hash=hash_value(otp),
        status=OtpStatus.ISSUED,
        created_at=now,
        expires_at=now + timedelta(minutes=5)
    )
    db.add(otp_entry)
    db.commit()

    # Send OTP
    if data.email:
        from app.controllers.auth.signup import send_email_otp
        send_email_otp(data.email, otp)
    elif data.phone:
        # TODO: Integrate SMS provider
        print(f"[DEV] Login OTP for {data.phone}: {otp}")

    return {"message": "Login OTP sent"}
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

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")  # fallback for dev
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
    token: str | None = None  # token is optional now

# ---------------------------
# Helpers
# ---------------------------
def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def create_jwt_token(user: User) -> str:
    """
    Create JWT token including user_type
    """
    user_id = str(user.id) if isinstance(user.id, uuid.UUID) else user.id
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "user_type": user.user_type.value,  # <-- include user_type
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# ---------------------------
# LOGIN ENDPOINT
# ---------------------------
@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):

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
        raise HTTPException(status_code=400, detail="User not registered. Please signup first")

    now = datetime.now(timezone.utc)

    # ---------------------------
    # PASSWORD LOGIN
    # ---------------------------
    if data.password:
        if user.password_hash != hash_value(data.password):
            raise HTTPException(status_code=400, detail="Invalid password")
        token = create_jwt_token(user)  # <-- pass full user object
        return LoginResponse(message="Login successful", token=token)

    # ---------------------------
    # OTP LOGIN / VERIFY OTP
    # ---------------------------
    if data.otp:
        # Verify OTP
        otp_entry = None
        if data.email:
            otp_entry = db.query(OtpSession).filter(
                OtpSession.email == data.email,
                OtpSession.purpose == OtpPurpose.LOGIN
            ).order_by(OtpSession.created_at.desc()).first()
        elif data.phone:
            otp_entry = db.query(OtpSession).filter(
                OtpSession.phone_e164 == data.phone,
                OtpSession.purpose == OtpPurpose.LOGIN
            ).order_by(OtpSession.created_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not found. Please request a new OTP")
        if otp_entry.expires_at < now:
            raise HTTPException(status_code=400, detail="OTP expired. Please request a new OTP")
        if otp_entry.otp_hash != hash_value(data.otp):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp_entry.status = OtpStatus.VERIFIED
        db.commit()

        token = create_jwt_token(user)  # <-- pass full user object
        return LoginResponse(message="Login successful", token=token)

    # ---------------------------
    # NO OTP PROVIDED → SEND OTP
    # ---------------------------
    otp = str(uuid.uuid4().int)[:6]
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

    return LoginResponse(message="OTP sent. Please verify to login.", token=None)
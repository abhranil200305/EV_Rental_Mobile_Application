# app/controllers/admin/login.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.schema import (
    OtpSession,
    OtpPurpose,
    OtpStatus,
    User,
    UserDevice,
    Session as UserSession,
    DevicePlatform,
    SessionStatus,
    UserType
)
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import hashlib
import os
import jwt
import uuid

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60


# ---------------------------
# Request Schema
# ---------------------------
class AdminLoginRequest(BaseModel):
    email: EmailStr
    otp: str | None = None
    password: str | None = None

    device_identifier: str | None = None
    platform: DevicePlatform | None = None
    device_name: str | None = None
    app_version: str | None = None
    os_version: str | None = None
    push_token: str | None = None


# ---------------------------
# Response Schema
# ---------------------------
class LoginResponse(BaseModel):
    message: str
    token: str | None = None


# ---------------------------
# Helpers
# ---------------------------
def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def create_jwt_token(user: User, session: UserSession) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "user_type": user.user_type.value,
        "jti": str(session.id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp()),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_or_update_user_device(db: Session, user: User, data: AdminLoginRequest):
    if not data.device_identifier:
        return None

    device = db.query(UserDevice).filter_by(
        user_id=user.id,
        device_identifier=data.device_identifier
    ).first()

    now = datetime.now(timezone.utc)

    if device:
        device.last_seen_at = now
        device.push_token = data.push_token or device.push_token
        device.app_version = data.app_version or device.app_version
        device.os_version = data.os_version or device.os_version
        device.device_name = data.device_name or device.device_name
        device.platform = data.platform or device.platform
    else:
        device = UserDevice(
            user_id=user.id,
            platform=data.platform or DevicePlatform.UNKNOWN,
            device_identifier=data.device_identifier,
            device_name=data.device_name,
            app_version=data.app_version,
            os_version=data.os_version,
            push_token=data.push_token,
            last_seen_at=now,
        )
        db.add(device)

    db.commit()
    return device


def create_user_session(db: Session, user: User, device: UserDevice | None):
    now = datetime.now(timezone.utc)

    session = UserSession(
        user_id=user.id,
        device_id=device.id if device else None,
        refresh_token_hash=str(uuid.uuid4()),
        access_token_jti=str(uuid.uuid4()),
        status=SessionStatus.ACTIVE,
        expires_at=now + timedelta(minutes=JWT_EXPIRE_MINUTES),
        last_seen_at=now,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


# ---------------------------
# ADMIN LOGIN ENDPOINT
# ---------------------------
@router.post("/login", response_model=LoginResponse)
def admin_login(data: AdminLoginRequest, db: Session = Depends(get_db)):

    # ---------------------------
    # FETCH ADMIN USER
    # ---------------------------
    user = db.query(User).filter(
        User.email == data.email,
        User.user_type == UserType.ADMIN   # 🔥 IMPORTANT
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Admin not found")

    now = datetime.now(timezone.utc)

    # ---------------------------
    # PASSWORD LOGIN
    # ---------------------------
    if data.password:
        if user.password_hash != hash_value(data.password):
            raise HTTPException(status_code=400, detail="Invalid password")

        device = create_or_update_user_device(db, user, data)
        session_obj = create_user_session(db, user, device)

        user.last_login_at = now
        db.commit()

        token = create_jwt_token(user, session_obj)

        return LoginResponse(message="Admin login successful", token=token)

    # ---------------------------
    # OTP LOGIN
    # ---------------------------
    if data.otp:

        # ⚠️ No email column in otp_sessions → fetch latest LOGIN OTP
        otp_entry = db.query(OtpSession).filter(
            OtpSession.purpose == OtpPurpose.LOGIN,
            OtpSession.status == OtpStatus.ISSUED
        ).order_by(OtpSession.created_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not found")

        if otp_entry.expires_at < now:
            otp_entry.status = OtpStatus.EXPIRED
            db.commit()
            raise HTTPException(status_code=400, detail="OTP expired")

        if otp_entry.otp_hash != hash_value(data.otp):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp_entry.status = OtpStatus.VERIFIED
        otp_entry.verified_at = now
        db.commit()

        device = create_or_update_user_device(db, user, data)
        session_obj = create_user_session(db, user, device)

        user.last_login_at = now
        db.commit()

        token = create_jwt_token(user, session_obj)

        return LoginResponse(message="Admin login successful", token=token)

    # ---------------------------
    # SEND OTP
    # ---------------------------
    otp = str(uuid.uuid4().int)[:6]

    otp_entry = OtpSession(
        id=uuid.uuid4(),
        phone_e164="",  # required
        purpose=OtpPurpose.LOGIN,
        otp_hash=hash_value(otp),
        status=OtpStatus.ISSUED,
        expires_at=now + timedelta(minutes=5),
    )

    db.add(otp_entry)
    db.commit()

    # send email
    from app.controllers.admin.signup import send_email_otp
    send_email_otp(data.email, otp)

    return LoginResponse(message="OTP sent. Verify to login.", token=None)
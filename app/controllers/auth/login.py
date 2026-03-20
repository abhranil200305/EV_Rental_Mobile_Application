# app/controllers/auth/login.py

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
)
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import hashlib
import os
import jwt
import uuid
import sqlalchemy as sa

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60


# ---------------------------
# Request Schema
# ---------------------------
class LoginRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
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
    user_id = str(user.id) if isinstance(user.id, uuid.UUID) else user.id
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "user_type": user.user_type.value,
        "jti": str(session.id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp()),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_or_update_user_device(db: Session, user: User, login_data: LoginRequest) -> UserDevice | None:
    if not login_data.device_identifier:
        return None

    device = db.query(UserDevice).filter_by(
        user_id=user.id, device_identifier=login_data.device_identifier
    ).first()

    now = datetime.now(timezone.utc)

    if device:
        device.last_seen_at = now
        device.push_token = login_data.push_token or device.push_token
        device.app_version = login_data.app_version or device.app_version
        device.os_version = login_data.os_version or device.os_version
        device.device_name = login_data.device_name or device.device_name
        device.platform = login_data.platform or device.platform
        db.commit()
    else:
        device = UserDevice(
            user_id=user.id,
            platform=login_data.platform or DevicePlatform.UNKNOWN,
            device_identifier=login_data.device_identifier,
            device_name=login_data.device_name,
            app_version=login_data.app_version,
            os_version=login_data.os_version,
            push_token=login_data.push_token,
            last_seen_at=now,
        )
        db.add(device)
        db.commit()

    return device


def create_user_session(db: Session, user: User, device: UserDevice | None) -> UserSession:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=JWT_EXPIRE_MINUTES)

    session = UserSession(
        user_id=user.id,
        device_id=device.id if device else None,
        refresh_token_hash=str(uuid.uuid4()),
        access_token_jti=str(uuid.uuid4()),
        status=SessionStatus.ACTIVE,
        expires_at=expires_at,
        last_seen_at=now,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


# ---------------------------
# LOGIN ENDPOINT
# ---------------------------
@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):

    if not any([data.email, data.phone]):
        raise HTTPException(status_code=400, detail="Email or phone required")

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

        device = create_or_update_user_device(db, user, data)
        session_obj = create_user_session(db, user, device)

        # 🔥 ADD THIS
        user.last_login_at = now
        db.commit()

        token = create_jwt_token(user, session_obj)

        return LoginResponse(message="Login successful", token=token)

    # ---------------------------
    # OTP LOGIN
    # ---------------------------
    if data.otp:
        otp_entry = None

        if data.email:
            otp_entry = (
                db.query(OtpSession)
                .filter(OtpSession.email == data.email, OtpSession.purpose == OtpPurpose.LOGIN)
                .order_by(OtpSession.created_at.desc())
                .first()
            )
        elif data.phone:
            otp_entry = (
                db.query(OtpSession)
                .filter(OtpSession.phone_e164 == data.phone, OtpSession.purpose == OtpPurpose.LOGIN)
                .order_by(OtpSession.created_at.desc())
                .first()
            )

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not found")
        if otp_entry.expires_at < now:
            raise HTTPException(status_code=400, detail="OTP expired")
        if otp_entry.otp_hash != hash_value(data.otp):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp_entry.status = OtpStatus.VERIFIED
        db.commit()

        device = create_or_update_user_device(db, user, data)
        session_obj = create_user_session(db, user, device)

        # 🔥 ADD THIS
        user.last_login_at = now
        db.commit()

        token = create_jwt_token(user, session_obj)

        return LoginResponse(message="Login successful", token=token)

    # ---------------------------
    # SEND OTP
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
        expires_at=now + timedelta(minutes=5),
    )

    db.add(otp_entry)
    db.commit()

    if data.email:
        from app.controllers.auth.signup import send_email_otp
        send_email_otp(data.email, otp)
    elif data.phone:
        print(f"[DEV] Login OTP for {data.phone}: {otp}")

    return LoginResponse(message="OTP sent. Please verify to login.", token=None)
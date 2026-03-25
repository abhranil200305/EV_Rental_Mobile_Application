# app/controllers/admin/signup.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.schema import (
    OtpSession, OtpPurpose, OtpStatus,
    UserType, UserStatus, User
)
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import random
import uuid
import hashlib
import smtplib
from email.message import EmailMessage
import os

router = APIRouter()


# ---------------------------
# Request Schema
# ---------------------------
class AdminSignupRequest(BaseModel):
    email: EmailStr
    otp: str | None = None
    password: str | None = None


# ---------------------------
# Helpers
# ---------------------------
def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ---------------------------
# Send OTP via Email
# ---------------------------
def send_email_otp(to_email: str, otp: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_user = os.getenv("HOSTINGER_EMAIL")
    smtp_password = os.getenv("HOSTINGER_PASS")

    print(f"[DEBUG] SMTP config: host={smtp_host}, port={smtp_port}, user={smtp_user}")

    if not all([smtp_host, smtp_user, smtp_password]):
        print("[WARN] SMTP config missing; skipping email send")
        return

    msg = EmailMessage()
    msg.set_content(f"Your Admin signup OTP is: {otp}\nValid for 5 minutes.")
    msg["Subject"] = "Admin Signup OTP"
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"[INFO] OTP sent to {to_email}")
    except Exception as e:
        print(f"[ERROR] Email send failed: {e}")


# ---------------------------
# ADMIN SIGNUP ENDPOINT
# ---------------------------
@router.post("/signup")
def admin_signup(data: AdminSignupRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)

    # ---------------------------
    # STEP 1: ISSUE OTP
    # ---------------------------
    if not data.otp and not data.password:

        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Admin already exists")

        otp = generate_otp()

        otp_entry = OtpSession(
            id=uuid.uuid4(),
            phone_e164="",
            email=data.email,
            purpose=OtpPurpose.SIGNUP,
            otp_hash=hash_value(otp),
            status=OtpStatus.ISSUED,
            created_at=now,
            expires_at=now + timedelta(minutes=5)
        )

        db.add(otp_entry)
        db.commit()

        print(f"[DEBUG] OTP for {data.email}: {otp}")
        send_email_otp(data.email, otp)

        return {"message": "OTP issued successfully"}

    # ---------------------------
    # STEP 2: VERIFY OTP
    # ---------------------------
    if data.otp and not data.password:

        otp_entry = db.query(OtpSession).filter(
            OtpSession.email == data.email,
            OtpSession.purpose == OtpPurpose.SIGNUP,
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

        return {"message": "OTP verified"}

    # ---------------------------
    # STEP 3: CREATE ADMIN USER
    # ---------------------------
    if data.otp and data.password:

        otp_entry = db.query(OtpSession).filter(
            OtpSession.email == data.email,
            OtpSession.purpose == OtpPurpose.SIGNUP,
            OtpSession.status == OtpStatus.VERIFIED
        ).order_by(OtpSession.created_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not verified")

        safe_phone = f"admin_{str(uuid.uuid4())[:8]}"

        user = User(
            id=uuid.uuid4(),
            email=data.email,
            phone_e164=safe_phone,
            password_hash=hash_value(data.password),
            user_type=UserType.ADMIN,
            status=UserStatus.ACTIVE,
            is_email_verified=True,
            created_at=now
        )

        db.add(user)
        db.commit()

        return {
            "message": "Admin signup successful"
        }

    # ---------------------------
    # INVALID FLOW
    # ---------------------------
    raise HTTPException(status_code=400, detail="Invalid request flow")
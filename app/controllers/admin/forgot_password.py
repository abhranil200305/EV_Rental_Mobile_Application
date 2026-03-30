# app/controllers/admin/forgot_password.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone
import hashlib, random, smtplib, os
from email.message import EmailMessage
import uuid

from app.db.database import get_db
from app.db.schema import User, UserType, OtpSession, OtpPurpose, OtpStatus

router = APIRouter(prefix="/admin", tags=["Admin"])

OTP_EXPIRY_MINUTES = 10


# ---------------------------
# Helpers
# ---------------------------
def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_email_otp(to_email: str, otp: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_user = os.getenv("HOSTINGER_EMAIL")
    smtp_password = os.getenv("HOSTINGER_PASS")

    msg = EmailMessage()
    msg.set_content(f"Your OTP for ADMIN password reset is: {otp}\nValid for {OTP_EXPIRY_MINUTES} minutes.")
    msg["Subject"] = "EV Rental ADMIN Password Reset OTP"
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"[INFO] OTP sent to {to_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email")


def send_sms_otp(phone: str, otp: str):
    # TODO: integrate MSG91
    print(f"[DEV] OTP for {phone}: {otp}")


# ---------------------------
# Request Schema
# ---------------------------
class ForgotPasswordFlow(BaseModel):
    email_or_phone: str
    otp: str = None
    new_password: str = None


# ---------------------------
# Admin Forgot Password Flow
# ---------------------------
@router.post("/forgot-password")
def admin_forgot_password(
    data: ForgotPasswordFlow,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)

    if not data.email_or_phone:
        raise HTTPException(status_code=400, detail="email_or_phone required")

    # ---------------------------
    # Get ADMIN user only
    # ---------------------------
    user = db.query(User).filter(
        or_(User.email == data.email_or_phone, User.phone_e164 == data.email_or_phone),
        User.user_type.in_([UserType.ADMIN, UserType.SUPERADMIN])
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    # ---------------------------
    # OTP VERIFY
    # ---------------------------
    if data.otp:
        otp_session = db.query(OtpSession).filter(
            OtpSession.phone_e164 == user.phone_e164,
            OtpSession.purpose == OtpPurpose.SENSITIVE_ACTION,
            OtpSession.status == OtpStatus.ISSUED,
            OtpSession.expires_at > now
        ).order_by(OtpSession.created_at.desc()).first()

        if not otp_session:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        if otp_session.otp_hash != hash_text(data.otp):
            otp_session.attempts += 1
            if otp_session.attempts >= otp_session.max_attempts:
                otp_session.status = OtpStatus.LOCKED
            db.commit()
            raise HTTPException(status_code=400, detail="Incorrect OTP")

        otp_session.status = OtpStatus.VERIFIED
        otp_session.verified_at = now
        db.commit()

        return {"message": "OTP verified successfully"}

    # ---------------------------
    # PASSWORD RESET
    # ---------------------------
    if data.new_password:
        otp_session = db.query(OtpSession).filter(
            OtpSession.phone_e164 == user.phone_e164,
            OtpSession.purpose == OtpPurpose.SENSITIVE_ACTION,
            OtpSession.status == OtpStatus.VERIFIED,
            OtpSession.expires_at > now
        ).order_by(OtpSession.verified_at.desc()).first()

        if not otp_session:
            raise HTTPException(status_code=400, detail="OTP verification required")

        user.password_hash = hash_text(data.new_password)
        db.commit()

        return {"message": "Admin password reset successfully"}

    # ---------------------------
    # SEND OTP
    # ---------------------------
    otp_code = generate_otp()

    otp_session = OtpSession(
        id=uuid.uuid4(),
        phone_e164=user.phone_e164,
        purpose=OtpPurpose.SENSITIVE_ACTION,
        otp_hash=hash_text(otp_code),
        status=OtpStatus.ISSUED,
        attempts=0,
        max_attempts=5,
        created_at=now,
        expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    )

    db.add(otp_session)
    db.commit()

    if "@" in data.email_or_phone:
        send_email_otp(user.email, otp_code)
    else:
        send_sms_otp(user.phone_e164, otp_code)

    return {"message": "OTP sent successfully"}
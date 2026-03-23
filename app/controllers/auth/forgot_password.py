# app/controllers/auth/forgot_password.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone
import hashlib, random, smtplib, os
from email.message import EmailMessage
import uuid

from app.db.database import get_db
from app.db.schema import User, OtpSession, OtpPurpose, OtpStatus

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_EXPIRY_MINUTES = 10

# ---------------------------
# Helpers
# ---------------------------
def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_email_otp(to_email: str, otp: str):
    """Send OTP via SMTP using environment variables"""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_user = os.getenv("HOSTINGER_EMAIL")
    smtp_password = os.getenv("HOSTINGER_PASS")

    msg = EmailMessage()
    msg.set_content(f"Your OTP for password reset is: {otp}\nIt is valid for {OTP_EXPIRY_MINUTES} minutes.")
    msg["Subject"] = "EV Rental Password Reset OTP"
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"[INFO] OTP sent to {to_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send OTP to {to_email}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email.")

def send_sms_otp(phone: str, otp: str):
    """Placeholder for SMS integration"""
    # TODO: integrate with MSG91 / Twilio
    print(f"[DEV] OTP for {phone}: {otp}")

# ---------------------------
# Request Schema
# ---------------------------
class ForgotPasswordFlow(BaseModel):
    step: str  # "request", "verify", "reset"
    email_or_phone: str = None
    otp: str = None
    otp_session_id: str = None
    new_password: str = None

# ---------------------------
# Forgot Password Endpoint
# ---------------------------
@router.post("/forgot-password")
def forgot_password_flow(data: ForgotPasswordFlow, db: Session = Depends(get_db)):
    step = data.step.lower()
    now = datetime.now(timezone.utc)

    # ---------------------------
    # STEP 1: REQUEST OTP
    # ---------------------------
    if step == "request":
        if not data.email_or_phone:
            raise HTTPException(status_code=400, detail="email_or_phone required")

        # Determine user by email or phone
        user = db.query(User).filter(
            or_(User.email == data.email_or_phone, User.phone_e164 == data.email_or_phone)
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        otp_code = generate_otp()
        otp_session = OtpSession(
            id=uuid.uuid4(),
            phone_e164=user.phone_e164,
            email=user.email,
            purpose=OtpPurpose.SENSITIVE_ACTION,
            otp_hash=hash_text(otp_code),
            status=OtpStatus.ISSUED,
            created_at=now,
            expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES)
        )
        db.add(otp_session)
        db.commit()

        # Send OTP to email or phone
        if "@" in data.email_or_phone:
            send_email_otp(data.email_or_phone, otp_code)
        else:
            send_sms_otp(data.email_or_phone, otp_code)

        return {"message": "OTP sent successfully"}

    # ---------------------------
    # STEP 2: VERIFY OTP
    # ---------------------------
    elif step == "verify":
        if not data.email_or_phone or not data.otp:
            raise HTTPException(status_code=400, detail="email_or_phone and otp required")

        # Check which identifier was used
        if "@" in data.email_or_phone:  # email OTP
            otp_session = db.query(OtpSession).filter(
                OtpSession.email == data.email_or_phone,
                OtpSession.status == OtpStatus.ISSUED,
                OtpSession.purpose == OtpPurpose.SENSITIVE_ACTION,
                OtpSession.expires_at > now
            ).order_by(OtpSession.created_at.desc()).first()
        else:  # phone OTP
            otp_session = db.query(OtpSession).filter(
                OtpSession.phone_e164 == data.email_or_phone,
                OtpSession.status == OtpStatus.ISSUED,
                OtpSession.purpose == OtpPurpose.SENSITIVE_ACTION,
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

        return {"message": "OTP verified successfully", "otp_session_id": str(otp_session.id)}

    # ---------------------------
    # STEP 3: RESET PASSWORD
    # ---------------------------
    elif step == "reset":
        if not data.otp_session_id or not data.new_password:
            raise HTTPException(status_code=400, detail="otp_session_id and new_password required")

        otp_session = db.query(OtpSession).filter(
            OtpSession.id == data.otp_session_id,
            OtpSession.status == OtpStatus.VERIFIED
        ).first()
        if not otp_session:
            raise HTTPException(status_code=400, detail="OTP not verified")

        # Determine user by email or phone from OTP session
        if otp_session.email:
            user = db.query(User).filter(User.email == otp_session.email).first()
        else:
            user = db.query(User).filter(User.phone_e164 == otp_session.phone_e164).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.password_hash = hash_text(data.new_password)
        db.commit()

        return {"message": "Password reset successfully"}

    else:
        raise HTTPException(status_code=400, detail="Invalid step")
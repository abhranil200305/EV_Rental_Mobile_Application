# app/controllers/auth/signup.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import schema
from app.db.schema import OtpSession, OtpPurpose, OtpStatus, UserType, UserStatus, KycStatus, KycCase
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
class SignupRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    otp: str | None = None
    password: str | None = None


# ---------------------------
# Helpers
# ---------------------------
def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def hash_value(value: str) -> str:
    """SHA256 hash"""
    return hashlib.sha256(value.encode()).hexdigest()


def get_identifier(data: SignupRequest) -> str:
    """Return identifier used for OTP: email or phone"""
    if data.email:
        return data.email
    if data.phone:
        return data.phone
    raise HTTPException(status_code=400, detail="Email or phone required")


# ---------------------------
# Send OTP via Email
# ---------------------------
def send_email_otp(to_email: str, otp: str):
    """Send OTP via SMTP using environment variables"""
    smtp_host = os.getenv("SMTP_HOST")           # e.g., smtp.hostinger.com
    smtp_port = int(os.getenv("SMTP_PORT", 465)) # SSL port
    smtp_user = os.getenv("HOSTINGER_EMAIL")
    smtp_password = os.getenv("HOSTINGER_PASS")

    msg = EmailMessage()
    msg.set_content(f"Your signup OTP is: {otp}\nIt is valid for 5 minutes.")
    msg["Subject"] = "Your Signup OTP"
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


# ---------------------------
# DRIVER SIGNUP ENDPOINT
# ---------------------------
@router.post("/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):

    identifier = get_identifier(data)
    now = datetime.now(timezone.utc)

    # ---------------------------
    # STEP 1: SEND OTP
    # ---------------------------
    if not data.otp and not data.password:
        query = db.query(schema.User)
        if data.email:
            query = query.filter(schema.User.email == data.email)
        elif data.phone:
            query = query.filter(schema.User.phone_e164 == data.phone)

        if query.first():
            raise HTTPException(status_code=400, detail="User already exists")

        otp = generate_otp()
        otp_entry = OtpSession(
            id=str(uuid.uuid4()),
            phone_e164=data.phone,
            email=data.email,
            purpose=OtpPurpose.SIGNUP,
            otp_hash=hash_value(otp),
            status=OtpStatus.ISSUED,
            created_at=now,
            expires_at=now + timedelta(minutes=5)
        )
        db.add(otp_entry)
        db.commit()

        # Send OTP
        if data.email:
            send_email_otp(data.email, otp)
        elif data.phone:
            # TODO: Integrate SMS provider
            print(f"[DEV] OTP for {data.phone}: {otp}")

        return {"message": "OTP sent"}

    # ---------------------------
    # STEP 2: VERIFY OTP
    # ---------------------------
    if data.otp and not data.password:
        otp_entry = None
        if data.phone:
            otp_entry = db.query(OtpSession).filter(
                OtpSession.phone_e164 == data.phone,
                OtpSession.purpose == OtpPurpose.SIGNUP,
                OtpSession.status == OtpStatus.ISSUED
            ).order_by(OtpSession.created_at.desc()).first()
        elif data.email:
            otp_entry = db.query(OtpSession).filter(
                OtpSession.email == data.email,
                OtpSession.purpose == OtpPurpose.SIGNUP,
                OtpSession.status == OtpStatus.ISSUED
            ).order_by(OtpSession.created_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not found")
        if otp_entry.expires_at < now:
            raise HTTPException(status_code=400, detail="OTP expired")
        if otp_entry.otp_hash != hash_value(data.otp):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp_entry.status = OtpStatus.VERIFIED
        db.commit()
        return {"message": "OTP verified"}

    # ---------------------------
    # STEP 3: SET PASSWORD AND CREATE DRIVER
    # ---------------------------
    if data.otp and data.password:
        otp_entry = None
        if data.phone:
            otp_entry = db.query(OtpSession).filter(
                OtpSession.phone_e164 == data.phone,
                OtpSession.purpose == OtpPurpose.SIGNUP,
                OtpSession.status == OtpStatus.VERIFIED
            ).order_by(OtpSession.created_at.desc()).first()
        elif data.email:
            otp_entry = db.query(OtpSession).filter(
                OtpSession.email == data.email,
                OtpSession.purpose == OtpPurpose.SIGNUP,
                OtpSession.status == OtpStatus.VERIFIED
            ).order_by(OtpSession.created_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not verified")

        # Insert new driver user
        user_data = {
            "id": str(uuid.uuid4()),
            "email": data.email,
            "phone_e164": data.phone,
            "password_hash": hash_value(data.password),
            "user_type": UserType.DRIVER,           # Correct user type
            "status": UserStatus.PENDING,           # Default status
            "kyc_status": KycStatus.KYC_NOT_STARTED,
            "created_at": now
        }

        user = schema.User(**user_data)
        db.add(user)
        db.commit()

        # Create empty KYC case
        kyc_case = KycCase(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status=KycStatus.KYC_NOT_STARTED,
            submitted_at=None,
            reviewed_at=None
        )
        db.add(kyc_case)
        db.commit()

        return {"message": "Driver signup successful", "user_id": user.id}

    # ---------------------------
    # INVALID CASE
    # ---------------------------
    raise HTTPException(status_code=400, detail="Invalid request flow")
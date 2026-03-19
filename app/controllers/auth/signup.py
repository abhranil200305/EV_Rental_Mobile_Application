# app/controllers/auth/signup.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.schema import OtpSession, OtpPurpose, OtpStatus, UserType, UserStatus, KycStatus, KycCase, User
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
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_user = os.getenv("HOSTINGER_EMAIL")
    smtp_password = os.getenv("HOSTINGER_PASS")

    # DEBUG: log SMTP config
    print(f"[DEBUG] SMTP config: host={smtp_host}, port={smtp_port}, user={smtp_user}")

    if not all([smtp_host, smtp_user, smtp_password]):
        print("[WARN] SMTP config missing; skipping email send")
        return

    msg = EmailMessage()
    msg.set_content(f"Your signup OTP is: {otp}\nIt is valid for 5 minutes.")
    msg["Subject"] = "Your Signup OTP"
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"[INFO] OTP sent via email to {to_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send OTP to {to_email}: {e}")
        # In dev, just log; do not raise exception


# ---------------------------
# DRIVER SIGNUP ENDPOINT
# ---------------------------
@router.post("/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    identifier = get_identifier(data)
    now = datetime.now(timezone.utc)

    # ---------------------------
    # STEP 1: ISSUE OTP
    # ---------------------------
    if not data.otp and not data.password:
        # Check if user already exists
        query = db.query(User)
        if data.email:
            query = query.filter(User.email == data.email)
        elif data.phone:
            query = query.filter(User.phone_e164 == data.phone)
        if query.first():
            raise HTTPException(status_code=400, detail="User already exists")

        otp = generate_otp()

        otp_entry = OtpSession(
            id=str(uuid.uuid4()),
            phone_e164=data.phone or "",
            email=data.email or "",
            purpose=OtpPurpose.SIGNUP,
            otp_hash=hash_value(otp),
            status=OtpStatus.ISSUED,
            created_at=now,
            expires_at=now + timedelta(minutes=5)
        )
        db.add(otp_entry)
        db.commit()

        # DEBUG: always print OTP for dev testing
        if data.email:
            print(f"[DEBUG] OTP for email {data.email}: {otp}")
            send_email_otp(data.email, otp)
        elif data.phone:
            print(f"[DEBUG] OTP for phone {data.phone}: {otp}")
            # TODO: integrate SMS provider

        return {"message": "OTP issued successfully"}

    # ---------------------------
    # STEP 2: VERIFY OTP
    # ---------------------------
    if data.otp and not data.password:
        otp_query = db.query(OtpSession).filter(
            OtpSession.purpose == OtpPurpose.SIGNUP,
            OtpSession.status == OtpStatus.ISSUED
        )
        if data.email:
            otp_entry = otp_query.filter(OtpSession.email == data.email).order_by(OtpSession.created_at.desc()).first()
        elif data.phone:
            otp_entry = otp_query.filter(OtpSession.phone_e164 == data.phone).order_by(OtpSession.created_at.desc()).first()
        else:
            otp_entry = None

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
    # STEP 3: CREATE DRIVER USER
    # ---------------------------
    if data.otp and data.password:
        otp_query = db.query(OtpSession).filter(
            OtpSession.purpose == OtpPurpose.SIGNUP,
            OtpSession.status == OtpStatus.VERIFIED
        )
        if data.email:
            otp_entry = otp_query.filter(OtpSession.email == data.email).order_by(OtpSession.created_at.desc()).first()
        elif data.phone:
            otp_entry = otp_query.filter(OtpSession.phone_e164 == data.phone).order_by(OtpSession.created_at.desc()).first()
        else:
            otp_entry = None

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not verified")

        # Create user
        user_data = {
            "id": str(uuid.uuid4()),
            "email": data.email,
            "phone_e164": data.phone,
            "password_hash": hash_value(data.password),
            "user_type": UserType.DRIVER,
            "status": UserStatus.PENDING,
            "kyc_status": KycStatus.KYC_NOT_STARTED,
            "created_at": now
        }
        user = User(**user_data)
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
    # INVALID FLOW
    # ---------------------------
    raise HTTPException(status_code=400, detail="Invalid request flow")
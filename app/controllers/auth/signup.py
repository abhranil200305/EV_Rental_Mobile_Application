from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import schema
from app.db.schema import OtpSession, OtpPurpose, OtpStatus
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import random
import uuid
import hashlib

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

def generate_otp():
    return str(random.randint(100000, 999999))


def hash_value(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def get_identifier(data: SignupRequest):
    if data.email:
        return data.email
    if data.phone:
        return data.phone
    raise HTTPException(status_code=400, detail="Email or phone required")


# ---------------------------
# SINGLE SIGNUP ENDPOINT
# ---------------------------

@router.post("/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):

    identifier = get_identifier(data)

    # ---------------------------
    # STEP 1: SEND OTP
    # ---------------------------
    if not data.otp and not data.password:

        # ✅ check if user already exists BEFORE sending OTP
        query = db.query(schema.User)
        if data.email:
            query = query.filter(schema.User.email == data.email)
        else:
            query = query.filter(schema.User.phone == data.phone)

        if query.first():
            raise HTTPException(status_code=400, detail="User already exists")

        otp = generate_otp()

        otp_entry = OtpSession(
            id=str(uuid.uuid4()),
            phone_e164=identifier,
            purpose=OtpPurpose.SIGNUP,
            otp_hash=hash_value(otp),
            status=OtpStatus.ISSUED,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5)  # ✅ expiry added
        )

        db.add(otp_entry)
        db.commit()

        print(f"OTP for {identifier}: {otp}")

        return {"message": "OTP sent"}

    # ---------------------------
    # STEP 2: VERIFY OTP
    # ---------------------------
    if data.otp and not data.password:

        otp_entry = db.query(OtpSession).filter(
            OtpSession.phone_e164 == identifier,
            OtpSession.purpose == OtpPurpose.SIGNUP,
            OtpSession.status == OtpStatus.ISSUED
        ).order_by(OtpSession.created_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not found")

        # ✅ expiry check
        if otp_entry.expires_at and otp_entry.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP expired")

        if otp_entry.otp_hash != hash_value(data.otp):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp_entry.status = OtpStatus.VERIFIED
        db.commit()

        return {"message": "OTP verified"}

    # ---------------------------
    # STEP 3: SET PASSWORD
    # ---------------------------
    if data.otp and data.password:

        otp_entry = db.query(OtpSession).filter(
            OtpSession.phone_e164 == identifier,
            OtpSession.purpose == OtpPurpose.SIGNUP,
            OtpSession.status == OtpStatus.VERIFIED
        ).order_by(OtpSession.created_at.desc()).first()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not verified")

        # ✅ FIXED QUERY (important)
        query = db.query(schema.User)
        if data.email:
            query = query.filter(schema.User.email == data.email)
        else:
            query = query.filter(schema.User.phone == data.phone)

        if query.first():
            raise HTTPException(status_code=400, detail="User already exists")

        user = schema.User(
            id=str(uuid.uuid4()),
            email=data.email,
            phone=data.phone,
            password_hash=hash_value(data.password),
            created_at=datetime.utcnow()
        )

        db.add(user)
        db.commit()

        return {"message": "Signup successful"}

    # ---------------------------
    # INVALID CASE
    # ---------------------------
    raise HTTPException(status_code=400, detail="Invalid request flow")
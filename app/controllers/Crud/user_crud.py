# app/controllers/Crud/user_crud.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import bcrypt
from datetime import date

from app.db.database import get_db
from app.db.schema import User, UserStatus, KycStatus
from app.schemas.user_schemas import (
    UserCreateSchema,
    UserUpdateSchema,
    UserResponseSchema
)

router = APIRouter(tags=["Users"])


# -------------------------
# Create User
# -------------------------
@router.post("/users", response_model=UserResponseSchema)
def create_user(user_data: UserCreateSchema, db: Session = Depends(get_db)):

    # Check phone
    existing_user = db.query(User).filter(User.phone_e164 == user_data.phone_e164).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Check email
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Password required
    if not user_data.password:
        raise HTTPException(status_code=400, detail="Password is required")

    # Hash password
    hashed_password = bcrypt.hashpw(
        user_data.password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    # Full name
    full_name = f"{user_data.first_name or ''} {user_data.last_name or ''}".strip()

    new_user = User(
        phone_e164=user_data.phone_e164.strip(),
        email=user_data.email,
        user_type=user_data.user_type,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        full_name=full_name,
        city=user_data.city,
        country_code=user_data.country_code or "IN",
        password_hash=hashed_password,
        status=UserStatus.PENDING,
        kyc_status=KycStatus.KYC_NOT_STARTED
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="User creation failed")

    return new_user


# -------------------------
# Get Single User
# -------------------------
@router.get("/users/{user_id}", response_model=UserResponseSchema)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.id == user_id,
        User.status != UserStatus.DELETED
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# -------------------------
# List Users
# -------------------------
@router.get("/users", response_model=List[UserResponseSchema])
def list_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):

    users = db.query(User).filter(
        User.status != UserStatus.DELETED
    ).offset(skip).limit(limit).all()

    return users


# -------------------------
# Update User Profile
# -------------------------
@router.put("/usersupdateprofile/{user_id}", response_model=UserResponseSchema)
def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdateSchema,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.id == user_id,
        User.status != UserStatus.DELETED
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # -------------------------
    # Email update
    # -------------------------
    if user_data.email is not None and user_data.email != user.email:
        existing_email = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()

        if existing_email:
            raise HTTPException(status_code=400, detail="Email already in use")

        user.email = user_data.email

    # -------------------------
    # Phone update
    # -------------------------
    if user_data.phone_e164 is not None and user_data.phone_e164 != user.phone_e164:
        existing_phone = db.query(User).filter(
            User.phone_e164 == user_data.phone_e164,
            User.id != user_id
        ).first()

        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already in use")

        user.phone_e164 = user_data.phone_e164.strip()

    # -------------------------
    # Update fields
    # -------------------------
    if user_data.first_name is not None:
        user.first_name = user_data.first_name

    if user_data.last_name is not None:
        user.last_name = user_data.last_name

    if user_data.address is not None:
        user.address_line1 = user_data.address

    if user_data.city is not None:
        user.city = user_data.city

    if user_data.kyc_status is not None:
        user.kyc_status = user_data.kyc_status

    # -------------------------
    # Date of Birth with validation
    # -------------------------
    if user_data.date_of_birth is not None:
        today = date.today()
        age = today.year - user_data.date_of_birth.year

        if age < 18:
            raise HTTPException(status_code=400, detail="User must be at least 18 years old")

        user.date_of_birth = user_data.date_of_birth

    # -------------------------
    # Update full name
    # -------------------------
    user.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    # -------------------------
    # Safe Commit
    # -------------------------
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="User update failed")

    return user


# -------------------------
# Delete User (Soft Delete)
# -------------------------
@router.delete("/users/{user_id}")
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.id == user_id,
        User.status != UserStatus.DELETED
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = UserStatus.DELETED

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="User delete failed")

    return {"detail": "User deactivated successfully"}
# app/schemas/user_schemas.py

from pydantic import BaseModel, EmailStr, StrictStr, validator
from typing import Optional
from uuid import UUID
from datetime import date

from app.db.schema import UserType, UserStatus, KycStatus


# -----------------------
# Create User
# -----------------------
class UserCreateSchema(BaseModel):
    phone_e164: StrictStr
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    user_type: UserType = UserType.DRIVER

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = "IN"

    @validator("phone_e164")
    def validate_phone_length(cls, v):
        if not (10 <= len(v) <= 20):
            raise ValueError("Phone number must be 10-20 characters")
        return v


# -----------------------
# Update User
# -----------------------
class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None

    email: Optional[EmailStr] = None
    phone_e164: Optional[StrictStr] = None

    address_line1: Optional[str] = None
    address_line2: Optional[str] = None

    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

    date_of_birth: Optional[date] = None

    # 🔥 IMPORTANT FIELD
    profile_photo_file_id: Optional[UUID] = None

    @validator("phone_e164")
    def validate_phone_length(cls, v):
        if v is not None and not (10 <= len(v) <= 20):
            raise ValueError("Phone number must be 10-20 characters")
        return v


# -----------------------
# Response (Driver View)
# -----------------------
class UserResponseSchema(BaseModel):
    id: UUID

    phone_e164: Optional[str]
    email: Optional[EmailStr]

    user_type: UserType
    status: UserStatus
    kyc_status: KycStatus

    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]

    address_line1: Optional[str]
    address_line2: Optional[str]

    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country_code: Optional[str]

    date_of_birth: Optional[date]

    is_phone_verified: Optional[bool]
    is_email_verified: Optional[bool]

    profile_photo_file_id: Optional[UUID]
    profile_photo_url: Optional[str] = None

    class Config:
        from_attributes = True
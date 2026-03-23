# app/controllers/user/userprofile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.database import get_db
from app.db.schema import User, FileObject
from app.utils.auth import get_current_user
from fastapi import Body

router = APIRouter(prefix="/user", tags=["User"])


# -----------------------------
# Helper: Generate file URL
# -----------------------------
def build_file_url(file_obj: Optional[FileObject]) -> Optional[str]:
    if not file_obj:
        return None
    # Assuming storage_uri = "/uploads/filename.jpg"
    return file_obj.storage_uri


# -----------------------------
# GET USER PROFILE
# -----------------------------
@router.get("/profile")
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch logged-in user's profile
    """

    # Fetch fresh user
    user: User = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get profile photo (if exists)
    profile_photo_url = None
    if user.profile_photo_file_id:
        file_obj: FileObject = db.query(FileObject).filter(
            FileObject.id == user.profile_photo_file_id
        ).first()
        profile_photo_url = build_file_url(file_obj)

    # Response
    return {
        "id": str(user.id),
        "phone_e164": user.phone_e164,
        "email": user.email,
        "user_type": user.user_type,
        "status": user.status,
        "kyc_status": user.kyc_status,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "date_of_birth": user.date_of_birth,
        "language_code": user.language_code,
        "address_line1": user.address_line1,
        "address_line2": user.address_line2,
        "city": user.city,
        "state": user.state,
        "postal_code": user.postal_code,
        "country_code": user.country_code,
        "is_phone_verified": user.is_phone_verified,
        "is_email_verified": user.is_email_verified,
        "profile_photo_file_id": str(user.profile_photo_file_id) if user.profile_photo_file_id else None,
        "profile_photo_url": profile_photo_url,
    }


# -----------------------------
# UPDATE USER PROFILE
# -----------------------------
@router.put("/profile")
def update_user_profile(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update logged-in user's profile
    """

    # Fetch fresh user
    user: User = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Fields allowed to update
    allowed_fields = [
        "first_name",
        "last_name",
        "full_name",
        "date_of_birth",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "profile_photo_file_id",
    ]

    for field in allowed_fields:
        if field in payload:
            setattr(user, field, payload[field])

    # Validate profile_photo_file_id if present
    if "profile_photo_file_id" in payload and payload["profile_photo_file_id"]:
        try:
            file_uuid = UUID(payload["profile_photo_file_id"])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid UUID format for profile_photo_file_id"
            )

        file_obj: FileObject = db.query(FileObject).filter(
            FileObject.id == file_uuid
        ).first()

        if not file_obj:
            raise HTTPException(
                status_code=400,
                detail="Invalid profile_photo_file_id"
            )

    # Commit changes
    db.commit()
    db.refresh(user)

    # Build profile photo URL
    profile_photo_url = None
    if user.profile_photo_file_id:
        file_obj: FileObject = db.query(FileObject).filter(
            FileObject.id == user.profile_photo_file_id
        ).first()
        profile_photo_url = build_file_url(file_obj)

    # Response
    return {
        "message": "Profile updated successfully",
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "profile_photo_file_id": str(user.profile_photo_file_id) if user.profile_photo_file_id else None,
        "profile_photo_url": profile_photo_url,
    }
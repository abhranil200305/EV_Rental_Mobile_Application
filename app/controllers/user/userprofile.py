# app/controllers/user/userprofile.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.db.schema import User, FileObject
from app.utils.auth import get_current_user

router = APIRouter(prefix="/user", tags=["User"])


# -----------------------------
# Helper: Generate file URL
# -----------------------------
def build_file_url(file_obj: Optional[FileObject]) -> Optional[str]:
    """
    Returns the accessible URL or storage path of the file.
    """
    if not file_obj:
        return None
    # Assuming storage_uri stores the relative path "/uploads/filename.jpg"
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
    Fetch the logged-in user's profile including profile photo.
    """
    # Fetch fresh user from DB
    user: User = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Use relationship to get profile photo
    profile_photo_url = build_file_url(user.profile_picture_file_object)

    # Response payload
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
        "profile_photo_file_id": str(user.profile_picture_file_object_id) if user.profile_picture_file_object_id else None,
        "profile_photo_url": profile_photo_url,
    }
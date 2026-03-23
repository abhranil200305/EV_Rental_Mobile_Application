# app/controllers/user/updateprofile.py

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.db.database import get_db
from app.db.schema import User, FileObject
from app.utils.auth import get_current_user

router = APIRouter(prefix="/user", tags=["User"])


# -----------------------------
# Helper: Generate file URL
# -----------------------------
def build_file_url(file_obj: Optional[FileObject]) -> Optional[str]:
    if not file_obj:
        return None
    return file_obj.storage_uri


# -----------------------------
# PATCH: UPDATE USER PROFILE
# -----------------------------
@router.patch("/updateprofile")
def update_user_profile(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update logged-in user's profile fields.
    Only allowed fields will be updated.
    Automatically updates full_name from first_name + last_name.
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
        "date_of_birth",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "profile_picture_file_object_id",
    ]

    # Update allowed fields
    for field in allowed_fields:
        if field in payload:
            setattr(user, field, payload[field])

    # Automatically update full_name from first_name + last_name
    user.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    # Validate profile_picture_file_object_id if provided
    if "profile_picture_file_object_id" in payload and payload["profile_picture_file_object_id"]:
        try:
            file_uuid = UUID(payload["profile_picture_file_object_id"])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid UUID format for profile_picture_file_object_id"
            )

        file_obj: FileObject = db.query(FileObject).filter(
            FileObject.id == file_uuid
        ).first()

        if not file_obj:
            raise HTTPException(
                status_code=400,
                detail="Invalid profile_picture_file_object_id"
            )

    # Commit changes
    db.commit()
    db.refresh(user)

    # Build profile photo URL
    profile_photo_url = build_file_url(user.profile_picture_file_object)

    # Response
    return {
        "message": "Profile updated successfully",
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "date_of_birth": user.date_of_birth,
        "address_line1": user.address_line1,
        "address_line2": user.address_line2,
        "city": user.city,
        "state": user.state,
        "postal_code": user.postal_code,
        "profile_photo_file_id": str(user.profile_picture_file_object_id) if user.profile_picture_file_object_id else None,
        "profile_photo_url": profile_photo_url,
    }
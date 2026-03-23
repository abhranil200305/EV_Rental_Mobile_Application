# app/controllers/Crud/user_crud.py
'''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.db.database import get_db
from app.db.schema import User, UserStatus, FileObject
from app.schemas.user_schemas import UserUpdateSchema, UserResponseSchema
from app.utils.auth import get_current_user

router = APIRouter(tags=["Users"])


# -------------------------
# Update My Profile (using JWT)
# -------------------------
@router.put("/users/updateprofile", response_model=UserResponseSchema)
def update_my_profile(
    user_data: UserUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the profile of the currently authenticated user.
    """

    # -------------------------
    # Fetch user
    # -------------------------
    user = db.query(User).filter(
        User.id == current_user.id,
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
            User.id != user.id
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
            User.id != user.id
        ).first()

        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already in use")

        user.phone_e164 = user_data.phone_e164.strip()

    # -------------------------
    # Other fields
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
    # Date of Birth validation
    # -------------------------
    if user_data.date_of_birth is not None:
        today = date.today()
        age = today.year - user_data.date_of_birth.year - (
            (today.month, today.day) < (user_data.date_of_birth.month, user_data.date_of_birth.day)
        )

        if age < 18:
            raise HTTPException(status_code=400, detail="User must be at least 18 years old")

        user.date_of_birth = user_data.date_of_birth

    # -------------------------
    # Profile Photo Update
    # -------------------------
    if user_data.profile_photo_file_id is not None:
        file_obj = db.query(FileObject).filter(
            FileObject.id == user_data.profile_photo_file_id
        ).first()

        if not file_obj:
            raise HTTPException(status_code=400, detail="Invalid file_id")

        if file_obj.uploaded_by_user_id != user.id:
            raise HTTPException(status_code=403, detail="Not your file")

        user.profile_photo_file_id = file_obj.id

    # -------------------------
    # Update full name
    # -------------------------
    user.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    # -------------------------
    # Safe commit
    # -------------------------
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="User update failed")

    # -------------------------
    # Build response safely
    # -------------------------
    user_response = UserResponseSchema(
        id=user.id,
        phone_e164=user.phone_e164,
        email=user.email,
        user_type=user.user_type,
        status=user.status,
        kyc_status=user.kyc_status,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        city=user.city,
        state=user.state,
        address_line1=user.address_line1,
        date_of_birth=user.date_of_birth,
        is_phone_verified=user.is_phone_verified,
        is_email_verified=user.is_email_verified,
        profile_photo_file_id=getattr(user, "profile_photo_file_id", None),
        profile_photo_url=None
    )

    # Optional: set profile photo URL if file exists
    if user_response.profile_photo_file_id:
        file_obj = db.query(FileObject).filter(FileObject.id == user_response.profile_photo_file_id).first()
        if file_obj:
            user_response.profile_photo_url = file_obj.storage_uri

    return user_response
    '''
from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user
from app.schemas.user_schemas import UserResponseSchema

router = APIRouter()


@router.get("/auth/me", response_model=UserResponseSchema)
def get_current_user_profile(current_user=Depends(get_current_user)):
    return UserResponseSchema(
        id=current_user.id,
        phone_e164=current_user.phone_e164,
        email=current_user.email,

        user_type=current_user.user_type,
        status=current_user.status,
        kyc_status=current_user.kyc_status,

        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,

        city=current_user.city,
        state=current_user.state,
        address_line1=current_user.address_line1,

        date_of_birth=current_user.date_of_birth,

        is_phone_verified=current_user.is_phone_verified,
        is_email_verified=current_user.is_email_verified,

        profile_photo_file_id=getattr(current_user, "profile_photo_file_id", None),

        # 🔥 IMPORTANT (you added this in schema)
        profile_photo_url=None
    )
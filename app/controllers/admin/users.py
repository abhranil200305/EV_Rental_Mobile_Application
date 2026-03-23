# app/controllers/admin/users.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from uuid import UUID
from app.db.database import get_db
from app.db.schema import User, UserType
from app.schemas import admin_schemas
from app.utils.auth import get_current_user  # JWT dependency

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])

@router.get("/batch", response_model=admin_schemas.UserListResponse)
def get_users_by_ids(
    user_ids: str = Query(..., description="Comma-separated user IDs"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Users per page"),
    current_admin: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch multiple users by user_ids (comma-separated) with pagination.
    Only accessible by ADMIN or SUPERADMIN users.
    Returns available users and list of IDs not found.
    """

    # ---------------------------
    # 1️⃣ Check admin privileges
    # ---------------------------
    if current_admin.user_type not in (UserType.ADMIN, UserType.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")

    # ---------------------------
    # 2️⃣ Split the comma-separated IDs
    # ---------------------------
    all_ids = [uid.strip() for uid in user_ids.split(",") if uid.strip()]

    # ---------------------------
    # 3️⃣ Pagination slicing
    # ---------------------------
    offset = (page - 1) * page_size
    end = offset + page_size
    paged_user_ids = all_ids[offset:end]

    # ---------------------------
    # 4️⃣ Validate UUIDs
    # ---------------------------
    valid_uuids = []
    invalid_uuids = []
    for uid in paged_user_ids:
        try:
            valid_uuids.append(UUID(uid))
        except ValueError:
            invalid_uuids.append(uid)

    # ---------------------------
    # 5️⃣ Query only valid UUIDs
    # ---------------------------
    users = db.query(User).filter(User.id.in_(valid_uuids)).all()
    users_map = {str(user.id): user for user in users}

    # ---------------------------
    # 6️⃣ Identify not found IDs
    # ---------------------------
    not_found_ids = invalid_uuids + [str(uid) for uid in valid_uuids if str(uid) not in users_map]

    # ---------------------------
    # 7️⃣ Serialize response
    # ---------------------------
    user_list = [
        admin_schemas.UserDetail(
            id=user.id,
            phone_e164=user.phone_e164,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            user_type=user.user_type,
            status=user.status,
            kyc_status=user.kyc_status,
            date_of_birth=user.date_of_birth,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        for user in users
    ]

    # ---------------------------
    # 8️⃣ Prepare totals
    # ---------------------------
    totals: Dict[str, int] = {
        "available_users": len(user_list),
        "not_found_users": len(not_found_ids)
    }

    # ---------------------------
    # 9️⃣ Return response
    # ---------------------------
    return admin_schemas.UserListResponse(
        users=user_list,
        not_found_ids=not_found_ids,
        page=page,
        page_size=page_size,
        total_users=totals
    )
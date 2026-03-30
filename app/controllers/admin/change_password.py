# app/controllers/admin/change_password.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib

from app.db.database import get_db
from app.db.schema import User, UserType
from app.utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


# =========================
# Request Schema
# =========================
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# =========================
# Admin Change Password API
# =========================
@router.post("/change-password")
def admin_change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Change password for logged-in ADMIN user only
    """

    # -------------------------
    # 0️⃣ Check ADMIN role
    # -------------------------
    if current_user.user_type not in [UserType.ADMIN, UserType.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can access this endpoint",
        )

    # -------------------------
    # 1️⃣ Verify current password
    # -------------------------
    current_hashed = hashlib.sha256(payload.current_password.encode()).hexdigest()
    if current_hashed != current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # -------------------------
    # 2️⃣ Prevent same password reuse
    # -------------------------
    new_hashed = hashlib.sha256(payload.new_password.encode()).hexdigest()
    if new_hashed == current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be same as old password",
        )

    # -------------------------
    # 3️⃣ Update password
    # -------------------------
    current_user.password_hash = new_hashed
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {"message": "Admin password changed successfully"}
# app/controllers/auth/change_password.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib

from app.db.database import get_db
from app.db.schema import User
from app.utils.auth import get_current_user  # JWT-authenticated user dependency

router = APIRouter(prefix="/auth", tags=["Auth"])

# =========================
# Request Schema
# =========================
class ChangePasswordRequest(BaseModel):
    current_password: str  # any string, number, short or long
    new_password: str      # any string, number, short or long

# =========================
# Change Password API
# =========================
@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Change password for logged-in user.
    Works with SHA-256 hashed passwords in DB.
    """

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
    # 2️⃣ Prevent reusing the same password
    # -------------------------
    new_hashed = hashlib.sha256(payload.new_password.encode()).hexdigest()
    if new_hashed == current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be same as old password",
        )

    # -------------------------
    # 3️⃣ Update DB with new SHA-256 hash
    # -------------------------
    current_user.password_hash = new_hashed
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {"message": "Password changed successfully"}
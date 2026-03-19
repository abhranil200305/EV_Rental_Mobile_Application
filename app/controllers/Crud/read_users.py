# app/controllers/Crud/read_users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.schema import User, UserType
from app.utils.auth import get_current_user  # Use the JWT dependency from auth.py

router = APIRouter(prefix="/admin", tags=["Admin Users"])

# ---------------------------
# GET ALL DRIVER IDS (ADMIN ONLY)
# ---------------------------
@router.get("/drivers", response_model=List[str])
def get_all_driver_ids(
    current_user: User = Depends(get_current_user),  # <-- JWT auth
    db: Session = Depends(get_db)
):
    """
    Fetch all driver user IDs. Only accessible by ADMIN or SUPERADMIN.
    JWT token required in Authorization header.
    """

    # Verify admin user_type
    if current_user.user_type not in (UserType.ADMIN, UserType.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")

    # Query all driver IDs
    driver_users = db.query(User.id).filter(User.user_type == UserType.DRIVER).all()

    # Extract UUIDs and convert to string
    driver_ids = [str(d.id) for d in driver_users]

    return driver_ids
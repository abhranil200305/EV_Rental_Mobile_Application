# app/controllers/Crud/read_users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.schema import User, UserType

router = APIRouter(prefix="/admin", tags=["Admin Users"])

# ---------------------------
# GET ALL DRIVER IDS (ADMIN ONLY)
# ---------------------------
@router.get("/drivers", response_model=List[str])
def get_all_driver_ids(admin_user_id: str, db: Session = Depends(get_db)):
    """
    Fetch all driver user IDs. Only accessible by ADMIN.
    `admin_user_id` is the requesting admin's user_id.
    """

    # Verify admin
    admin_user = db.query(User).filter(User.id == admin_user_id).first()
    if not admin_user or (hasattr(admin_user.user_type, "name") and admin_user.user_type.name != "ADMIN") and str(admin_user.user_type) != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")

    # Query all driver IDs
    driver_users = db.query(User.id).filter(User.user_type == UserType.DRIVER).all()

    # Extract UUIDs and convert to string
    driver_ids = [str(d.id) for d in driver_users]

    return driver_ids
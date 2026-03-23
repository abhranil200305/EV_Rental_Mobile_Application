# app/controllers/user/file_access.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.db.database import get_db
from app.db.schema import FileObject, User
from app.utils.auth import get_current_user  # This returns User object from JWT

router = APIRouter(prefix="/user", tags=["File Access"])


# -----------------------------
# GET: Serve Logged-in User Profile Photo
# -----------------------------
@router.get("/profilephoto")
def get_profile_photo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the logged-in user's profile photo securely.
    DRIVER can only access their own photo.
    ADMIN can access any user's photo.
    """
    if not current_user.profile_picture_file_object_id:
        raise HTTPException(status_code=404, detail="Profile photo not set")

    # Fetch FileObject
    file_obj: FileObject = db.query(FileObject).filter(
        FileObject.id == current_user.profile_picture_file_object_id
    ).first()

    if not file_obj:
        raise HTTPException(status_code=404, detail="Profile photo file not found")

    # DRIVER restriction (redundant here because it's their own file)
    if current_user.user_type.name == "DRIVER":
        if file_obj.uploaded_by_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed to access this file")

    # ADMIN can access any file (already handled)

    # Check if file exists on disk
    if not os.path.exists(file_obj.storage_uri):
        raise HTTPException(status_code=404, detail="File not found on server")

    # Serve file directly
    return FileResponse(file_obj.storage_uri)
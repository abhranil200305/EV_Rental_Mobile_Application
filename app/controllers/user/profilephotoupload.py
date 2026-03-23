# app/controllers/user/profilephotoupload.py

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
import hashlib

from app.db.database import get_db
from app.db.schema import User, FileObject
from app.utils.auth import get_current_user

router = APIRouter(prefix="/user", tags=["User"])

UPLOAD_DIR = "uploads/profile_photos"

# -----------------------------
# Helper: build file URL
# -----------------------------
def build_file_url(file_obj: Optional[FileObject]) -> Optional[str]:
    if not file_obj:
        return None
    return file_obj.storage_uri

# -----------------------------
# POST: Upload profile photo
# -----------------------------
@router.post("/profilephotoupload")
def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a profile photo, save FileObject, link it to the user.
    """
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # Save file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Compute SHA256 checksum
    file.file.seek(0)
    file_bytes = file.file.read()
    checksum = hashlib.sha256(file_bytes).hexdigest()

    # Insert into FileObject table
    file_obj = FileObject(
        storage_uri=file_path,
        file_name=file.filename,
        mime_type=file.content_type,
        checksum_sha256=checksum,
        size_bytes=len(file_bytes),
        purpose="OTHER",
        uploaded_by_user_id=current_user.id,
        metadata_json={}
    )
    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)

    # Link the uploaded photo to user
    current_user.profile_picture_file_object_id = file_obj.id
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile photo uploaded successfully",
        "profile_photo_file_id": str(file_obj.id),
        "profile_photo_url": build_file_url(file_obj)
    }
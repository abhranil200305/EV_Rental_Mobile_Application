# app/controllers/user/profilephotoupload.py

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
import hashlib
import uuid

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
# Generate SHA256 checksum
# -----------------------------
def generate_checksum(file: UploadFile):
    hasher = hashlib.sha256()
    file.file.seek(0)

    while chunk := file.file.read(8192):
        hasher.update(chunk)

    file.file.seek(0)
    return hasher.hexdigest()


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
    Upload a profile photo with ownership-based duplicate handling.
    """

    # ✅ Validate image type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail="Only JPG/PNG images are allowed"
        )

    # Ensure upload directory exists
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # ✅ Generate checksum
    checksum = generate_checksum(file)

    # ✅ Check duplicate file
    existing_file = db.query(FileObject).filter(
        FileObject.checksum_sha256 == checksum
    ).first()

    if existing_file:
        # 🔥 CASE 1: Same user → allow reuse
        if existing_file.uploaded_by_user_id == current_user.id:
            current_user.profile_picture_file_object_id = existing_file.id
            db.commit()
            db.refresh(current_user)

            return {
                "message": "Profile photo already exists, reused successfully",
                "profile_photo_file_id": str(existing_file.id),
                "profile_photo_url": build_file_url(existing_file)
            }

        # ❌ CASE 2: Different user → block
        else:
            raise HTTPException(
                status_code=403,
                detail="Please upload your own profile photo"
            )

    # ✅ Save new file (unique filename)
    ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # ✅ Insert into DB
    file_obj = FileObject(
        storage_uri=file_path,
        file_name=file.filename,
        mime_type=file.content_type,
        checksum_sha256=checksum,
        size_bytes=os.path.getsize(file_path),
        purpose="PROFILE_PICTURE",
        uploaded_by_user_id=current_user.id,
        metadata_json={}
    )

    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)

    # ✅ Link to user
    current_user.profile_picture_file_object_id = file_obj.id
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile photo uploaded successfully",
        "profile_photo_file_id": str(file_obj.id),
        "profile_photo_url": build_file_url(file_obj)
    }
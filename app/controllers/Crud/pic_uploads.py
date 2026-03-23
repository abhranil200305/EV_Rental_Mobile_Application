# app/controllers/Crud/pic_uploads.py
'''
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import uuid
import hashlib

from app.db.database import get_db
from app.db.schema import FileObject, FilePurpose, User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/files", tags=["File Uploads"])

UPLOAD_DIR = "Pic_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -------------------------
# Generate SHA256 checksum
# -------------------------
def generate_checksum(file: UploadFile):
    hasher = hashlib.sha256()
    file.file.seek(0)

    while chunk := file.file.read(8192):
        hasher.update(chunk)

    file.file.seek(0)
    return hasher.hexdigest()


# -------------------------
# Upload Multiple Images
# -------------------------
@router.post("/upload")
def upload_images(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = []

    for file in files:

        # ✅ Validate image type
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} is not a valid image"
            )

        # ✅ Generate checksum
        checksum = generate_checksum(file)

        # ✅ Check duplicate
        existing = db.query(FileObject).filter(
            FileObject.checksum_sha256 == checksum
        ).first()

        if existing:
            results.append({
                "file_id": str(existing.id),
                "file_url": existing.storage_uri,
                "message": "Already exists"
            })
            continue

        # ✅ Save file locally
        ext = file.filename.split(".")[-1]
        new_filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, new_filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        file_url = f"/uploads/{new_filename}"

        # ✅ Save to DB
        file_obj = FileObject(
            storage_uri=file_url,
            file_name=file.filename,
            mime_type=file.content_type,
            checksum_sha256=checksum,
            size_bytes=os.path.getsize(file_path),
            purpose=FilePurpose.OTHER,  # change later if needed
            uploaded_by_user_id=current_user.id
        )

        db.add(file_obj)
        db.commit()
        db.refresh(file_obj)

        results.append({
            "file_id": str(file_obj.id),
            "file_url": file_url
        })

    return {
        "files": results
    }
'''
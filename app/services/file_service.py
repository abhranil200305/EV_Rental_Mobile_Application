# app/services/file_service.py

import hashlib
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from typing import Optional
import uuid

from app.db.schema import FileObject, FilePurpose
from app.services.storage.local_storage import save_file


def create_file_object(
    db: Session,
    file: UploadFile,
    user_id: Optional[uuid.UUID],
    purpose: FilePurpose = FilePurpose.KYC_DOCUMENT
) -> FileObject:
    """
    Creates a FileObject entry after saving the file.

    Parameters:
    - db: DB session
    - file: UploadFile
    - user_id: UUID of uploader (can be None)
    - purpose: FilePurpose (default = KYC_DOCUMENT)

    Returns:
    - FileObject
    """

    # -------------------------
    # 1️⃣ Validate filename
    # -------------------------
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name"
        )

    # -------------------------
    # 2️⃣ Read file safely
    # -------------------------
    try:
        file_bytes = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file"
        )

    # Reset pointer (important if reused elsewhere)
    file.file.seek(0)

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded"
        )

    # -------------------------
    # 3️⃣ File validations
    # -------------------------
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )

    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type"
        )

    # -------------------------
    # 4️⃣ Generate checksum
    # -------------------------
    checksum = hashlib.sha256(file_bytes).hexdigest()

    # -------------------------
    # 5️⃣ Deduplication (Optional but useful)
    # -------------------------
    existing_file = db.query(FileObject).filter(
        FileObject.checksum_sha256 == checksum
    ).first()

    if existing_file:
        return existing_file

    # -------------------------
    # 6️⃣ Save file to storage
    # -------------------------
    try:
        file_path = save_file(file_bytes, file.filename)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store file"
        )

    # -------------------------
    # 7️⃣ Create DB record
    # -------------------------
    file_obj = FileObject(
        storage_uri=file_path,
        file_name=file.filename,
        mime_type=file.content_type,
        checksum_sha256=checksum,
        size_bytes=len(file_bytes),
        purpose=purpose,
        uploaded_by_user_id=user_id,
    )

    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)

    return file_obj
# app/controllers/kyc/file_access.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from uuid import UUID

from app.db.database import get_db
from app.db.schema import (
    FileObject,
    KycDocument,
    KycCase,
    User
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/user/kyc", tags=["KYC File Access"])


# -----------------------------
# GET: Serve ONE KYC Document BY ID
# -----------------------------
@router.get("/file/{kyc_document_id}")
def get_kyc_file(
    kyc_document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return ONE KYC document using kyc_document_id

    DRIVER → only own docs
    ADMIN → can access any user's docs
    """

    # 1️⃣ Get KYC Document
    kyc_doc: KycDocument = db.query(KycDocument).filter(
        KycDocument.id == kyc_document_id
    ).first()

    if not kyc_doc:
        raise HTTPException(status_code=404, detail="KYC document not found")

    # 2️⃣ Get KYC Case
    kyc_case: KycCase = db.query(KycCase).filter(
        KycCase.id == kyc_doc.kyc_case_id
    ).first()

    if not kyc_case:
        raise HTTPException(status_code=404, detail="KYC case not found")

    # 3️⃣ 🔐 SECURITY CHECK
    if current_user.user_type.name == "DRIVER":
        if kyc_case.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed to access this file")

    # ADMIN → allowed

    # 4️⃣ Get FileObject
    file_obj: FileObject = db.query(FileObject).filter(
        FileObject.id == kyc_doc.file_id
    ).first()

    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # 5️⃣ Check file exists on disk
    if not os.path.exists(file_obj.storage_uri):
        raise HTTPException(status_code=404, detail="File not found on server")

    # 6️⃣ Return file
    return FileResponse(
        path=file_obj.storage_uri,
        media_type=file_obj.mime_type,
        filename=file_obj.file_name
    )
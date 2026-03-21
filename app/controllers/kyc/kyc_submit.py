from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.db.database import get_db
from app.db.schema import User, KycCase, KycDocument, KycStatus
from app.services.file_service import save_file
from app.utils.auth import get_current_user
from app.schemas.kyc_schemas import KycSubmitResponse

router = APIRouter()


@router.post("/kyc/submit", response_model=KycSubmitResponse)
async def submit_kyc(
    doc_types: List[str] = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit KYC documents for verification:
    - doc_types: list of document types matching uploaded files
    - files: list of uploaded documents (JPG, PNG, PDF)
    """

    # Validation: number of files matches number of doc_types
    if len(doc_types) != len(files):
        raise HTTPException(status_code=400, detail="Mismatch in files and doc_types")

    # Create a new KYC case
    kyc_case = KycCase(
        id=uuid.uuid4(),
        user_id=current_user.id,
        status=KycStatus.KYC_SUBMITTED,
        submitted_at=datetime.utcnow()
    )
    db.add(kyc_case)
    db.flush()  # ensures kyc_case.id is available

    # Save each file and create KycDocument
    for doc_type, file in zip(doc_types, files):
        file_obj = save_file(file, db)  # calls local_storage or S3 based on config

        kyc_doc = KycDocument(
            id=uuid.uuid4(),
            kyc_case_id=kyc_case.id,
            doc_type=doc_type,
            file_id=file_obj.id,
            verified_bool=False
        )
        db.add(kyc_doc)

    # Update user's KYC status
    current_user.kyc_status = KycStatus.KYC_SUBMITTED

    # Commit all changes
    db.commit()

    return {"message": "KYC submitted successfully", "kyc_case_id": kyc_case.id}
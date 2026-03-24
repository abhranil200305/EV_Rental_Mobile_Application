# app/controllers/kyc/kyc_status.py
'''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schema import KycCase, User, FileObject
from app.schemas.kyc_schemas import (
    KycStatusResponse,
    KycDocumentStatus,
    KycReviewStatus
)
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/kyc/status", response_model=KycStatusResponse)
def get_kyc_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    kyc_case = db.query(KycCase).filter(
        KycCase.user_id == current_user.id
    ).order_by(KycCase.created_at.desc()).first()

    if not kyc_case:
        raise HTTPException(status_code=404, detail="No KYC found")

    documents = []
    for doc in kyc_case.documents:
        file_obj = db.query(FileObject).filter(
            FileObject.id == doc.file_id
        ).first()

        documents.append(KycDocumentStatus(
            doc_type=doc.doc_type,
            verified=doc.verified_bool,
            file_uri=file_obj.storage_uri if file_obj else None
        ))

    reviews = []
    for review in kyc_case.reviews:
        reviews.append(KycReviewStatus(
            reviewer_id=review.reviewer_id,
            notes=review.notes,
            status=review.to_status,
            reason_code=review.reason_code
        ))

    return KycStatusResponse(
        current_status=kyc_case.status,
        documents=documents,
        reviews=reviews
    )'''
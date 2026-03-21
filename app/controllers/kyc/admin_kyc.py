from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from app.db.database import get_db
from app.db.schema import KycCase, KycReview, KycStatus, User
from app.schemas.kyc_schemas import AdminKycReviewRequest, AdminKycQueueItem
from app.utils.auth import get_current_user

router = APIRouter()


# -----------------------------
# GET: Admin KYC queue
# -----------------------------
@router.get("/admin/kyc/queue", response_model=List[AdminKycQueueItem])
def get_kyc_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only admin users
    if current_user.user_type not in ["ADMIN", "SUPERADMIN", "SUPPORT"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Query all pending KYC cases
    kyc_cases = db.query(KycCase).join(User).filter(
        KycCase.status == KycStatus.KYC_SUBMITTED
    ).all()

    queue = []
    for case in kyc_cases:
        queue.append(AdminKycQueueItem(
            kyc_case_id=case.id,
            user_id=case.user_id,
            user_full_name=case.user.full_name,
            status=case.status,
            submitted_at=case.submitted_at
        ))
    return queue


# -----------------------------
# POST: Admin KYC review
# -----------------------------
@router.post("/admin/kyc/review")
def review_kyc(
    payload: AdminKycReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization
    if current_user.user_type not in ["ADMIN", "SUPERADMIN", "SUPPORT"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Fetch the KYC case
    kyc_case = db.query(KycCase).filter(KycCase.id == payload.kyc_case_id).first()
    if not kyc_case:
        raise HTTPException(status_code=404, detail="KYC case not found")

    # Create KYC review record
    review = KycReview(
        id=uuid.uuid4(),
        kyc_case_id=kyc_case.id,
        reviewer_id=current_user.id,
        from_status=kyc_case.status,
        to_status=payload.to_status,
        reason_code=payload.reason_code,
        notes=payload.notes
    )
    db.add(review)

    # Update KYC case status
    kyc_case.status = payload.to_status
    kyc_case.reviewed_at = datetime.utcnow()
    kyc_case.reviewer_id = current_user.id
    kyc_case.reject_reason_code = payload.reason_code
    kyc_case.reject_reason_text = payload.notes

    # Update user's KYC status
    kyc_case.user.kyc_status = payload.to_status

    db.commit()
    return {"message": "KYC reviewed successfully", "kyc_case_id": kyc_case.id}
from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import datetime
from app.db.schema import KycStatus, KycDocType, KycRejectReasonCode

# -----------------------------
# User submits KYC
# -----------------------------
class KycSubmitResponse(BaseModel):
    message: str
    kyc_case_id: UUID4

# -----------------------------
# User views KYC status
# -----------------------------
class KycDocumentStatus(BaseModel):
    doc_type: KycDocType
    verified: bool
    file_uri: Optional[str]

class KycReviewStatus(BaseModel):
    reviewer_id: UUID4
    notes: Optional[str]
    status: KycStatus
    reason_code: Optional[KycRejectReasonCode]

class KycStatusResponse(BaseModel):
    current_status: KycStatus
    documents: List[KycDocumentStatus]
    reviews: List[KycReviewStatus]

# -----------------------------
# Admin reviews KYC
# -----------------------------
class AdminKycReviewRequest(BaseModel):
    kyc_case_id: UUID4
    to_status: KycStatus
    reason_code: Optional[KycRejectReasonCode]
    notes: Optional[str]

class AdminKycQueueItem(BaseModel):
    kyc_case_id: UUID4
    user_id: UUID4
    user_full_name: Optional[str]
    status: KycStatus
    submitted_at: Optional[datetime]
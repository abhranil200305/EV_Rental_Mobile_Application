# app/controllers/kyc/user_kyc.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import hashlib
import os

from app.db.database import get_db
from app.db.schema import (
    User, KycCase, KycDocument, FileObject,
    KycStatus, KycDocType, FilePurpose, UserConsent, ConsentStatus
)
from app.services.storage.local_storage import save_file
from app.controllers.kyc.helpers import (
    get_current_user,
    get_editable_kyc_case_for_user,
    ensure_case_belongs_to_user,
    ensure_case_editable,
    create_or_get_file_object,
    required_doc_types_for_user,
    build_kyc_response
)

router = APIRouter(prefix="/user/kyc", tags=["KYC User"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "kyc_documents")


# -----------------------------
# Get current KYC summary
# -----------------------------
@router.get("/", response_model=dict)
def get_user_kyc_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_editable_kyc_case_for_user(user.id)
    return build_kyc_response(db, user, case)


# -----------------------------
# Start a new KYC case if none editable exists
# -----------------------------
@router.post("/cases", response_model=dict)
def start_kyc_case(source: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_editable_kyc_case_for_user(user.id)
    if case:
        return build_kyc_response(db, user, case)

    # Create new case
    case = KycCase(
        user_id=user.id,
        status=KycStatus.KYC_IN_PROGRESS,
        source=source,
        submitted_at=None
    )
    db.add(case)
    if user.kyc_status == KycStatus.KYC_NOT_STARTED:
        user.kyc_status = KycStatus.KYC_IN_PROGRESS
    db.commit()
    db.refresh(case)
    return build_kyc_response(db, user, case)


# -----------------------------
# Upsert consents
# -----------------------------
@router.post("/consents", response_model=dict)
def upsert_user_consents(consents: list[dict], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for consent in consents:
        consent_type = consent.get("consent_type")
        status = consent.get("status")
        if status not in ConsentStatus.__members__:
            raise HTTPException(status_code=400, detail=f"Invalid consent status: {status}")
        db_consent = db.query(UserConsent).filter_by(user_id=user.id, consent_type=consent_type).first()
        now = datetime.utcnow()
        if db_consent:
            db_consent.status = ConsentStatus(status)
            if db_consent.status == ConsentStatus.GRANTED:
                db_consent.granted_at = now
                db_consent.withdrawn_at = None
            else:
                db_consent.withdrawn_at = now
        else:
            db_consent = UserConsent(
                user_id=user.id,
                consent_type=consent_type,
                status=ConsentStatus(status),
                granted_at=now if status == ConsentStatus.GRANTED else None,
                withdrawn_at=now if status == ConsentStatus.WITHDRAWN else None,
                version="1.0",
                source="user_app"
            )
            db.add(db_consent)
    db.commit()
    return {"message": "Consents updated"}


# -----------------------------
# Upload or replace a KYC document
# -----------------------------
@router.put("/documents/{doc_type}", response_model=dict)
async def upload_or_replace_kyc_document(
    doc_type: KycDocType,
    kyc_case_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    case = get_editable_kyc_case_for_user(user.id)
    if not case or case.id != kyc_case_id:
        raise HTTPException(status_code=403, detail="Case not editable or does not belong to user.")

    ensure_case_editable(case)

    # Save file locally
    file_bytes = await file.read()
    saved_path, metadata = save_file(file_bytes, file.filename)

    # Compute checksum
    checksum = hashlib.sha256(file_bytes).hexdigest()
    metadata.update({"checksum_sha256": checksum, "uploaded_by_user_id": str(user.id)})

    # Create or reuse file_object
    file_obj = create_or_get_file_object(
        db,
        storage_uri=saved_path,
        file_name=file.filename,
        mime_type=file.content_type,
        checksum_sha256=checksum,
        size_bytes=len(file_bytes),
        purpose=FilePurpose.KYC_SELFIE if doc_type == KycDocType.SELFIE else FilePurpose.KYC_DOCUMENT,
        uploaded_by_user_id=user.id,
        metadata_json=metadata
    )

    # Create or replace kyc_document
    kyc_doc = db.query(KycDocument).filter_by(kyc_case_id=case.id, doc_type=doc_type).first()
    if kyc_doc:
        kyc_doc.file_id = file_obj.id
        kyc_doc.verified_bool = False
        kyc_doc.document_number_masked = None
        kyc_doc.expiry_date = None
        kyc_doc.extracted_fields_json = {}
    else:
        kyc_doc = KycDocument(
            kyc_case_id=case.id,
            doc_type=doc_type,
            file_id=file_obj.id,
            verified_bool=False,
            document_number_masked=None,
            expiry_date=None,
            extracted_fields_json={}
        )
        db.add(kyc_doc)

    # If case was NEEDS_ACTION, move to IN_PROGRESS
    if case.status == KycStatus.KYC_NEEDS_ACTION:
        case.status = KycStatus.KYC_IN_PROGRESS

    db.commit()
    db.refresh(kyc_doc)
    return build_kyc_response(db, user, case)


# -----------------------------
# Delete a KYC document
# -----------------------------
@router.delete("/documents/{doc_type}", response_model=dict)
def delete_kyc_document(doc_type: KycDocType, kyc_case_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_editable_kyc_case_for_user(user.id)
    if not case or case.id != kyc_case_id:
        raise HTTPException(status_code=403, detail="Case not editable or does not belong to user.")

    ensure_case_editable(case)
    kyc_doc = db.query(KycDocument).filter_by(kyc_case_id=case.id, doc_type=doc_type).first()
    if kyc_doc:
        db.delete(kyc_doc)
        db.commit()
    return build_kyc_response(db, user, case)


# -----------------------------
# Submit KYC case
# -----------------------------
@router.post("/submit", response_model=dict)
def submit_kyc_case(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_editable_kyc_case_for_user(user.id)
    if not case:
        raise HTTPException(status_code=400, detail="No editable KYC case found.")

    ensure_case_editable(case)

    # Validate required documents
    required_docs = required_doc_types_for_user()
    existing_docs = {doc.doc_type for doc in case.kyc_documents}
    missing_docs = [d.value for d in required_docs if d not in existing_docs]
    if missing_docs:
        raise HTTPException(status_code=400, detail=f"Missing required documents: {missing_docs}")

    # Validate consents
    consents = db.query(UserConsent).filter_by(user_id=user.id).all()
    for consent in consents:
        if consent.status != ConsentStatus.GRANTED:
            raise HTTPException(status_code=400, detail=f"Consent {consent.consent_type.value} not granted.")

    # Submit case
    case.status = KycStatus.KYC_SUBMITTED
    case.submitted_at = datetime.utcnow()
    user.kyc_status = KycStatus.KYC_SUBMITTED

    db.commit()
    db.refresh(case)
    return build_kyc_response(db, user, case)
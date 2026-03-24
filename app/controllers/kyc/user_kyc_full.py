# app/controllers/kyc/user_kyc_full.py

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone, date
import os
import hashlib
import uuid as py_uuid
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.db.schema import (
    User, KycCase, KycDocument, FileObject,
    KycStatus, KycDocType, FilePurpose,
    UserConsent, ConsentStatus, ConsentType, ConsentSource
)
from app.utils.auth import get_current_user

# -----------------------------
# Constants
# -----------------------------
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "kyc_documents")

# -----------------------------
# Helper functions
# -----------------------------
def save_file(file_bytes: bytes, original_filename: str):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(original_filename)[1]
    server_filename = f"{py_uuid.uuid4().hex}{ext}"
    storage_path = os.path.join(UPLOAD_DIR, server_filename)
    with open(storage_path, "wb") as f:
        f.write(file_bytes)
    metadata = {
        "original_file_name": original_filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    return storage_path, metadata


def create_or_get_file_object(db: Session, storage_uri: str, file_name: str, mime_type: str,
                              checksum_sha256: str, size_bytes: int, purpose: FilePurpose,
                              uploaded_by_user_id: py_uuid.UUID, metadata_json: dict):
    existing = db.query(FileObject).filter_by(checksum_sha256=checksum_sha256).first()
    if existing:
        return existing
    file_obj = FileObject(
        storage_uri=storage_uri,
        file_name=file_name,
        mime_type=mime_type,
        checksum_sha256=checksum_sha256,
        size_bytes=size_bytes,
        purpose=purpose,
        uploaded_by_user_id=uploaded_by_user_id,
        metadata_json=metadata_json
    )
    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)
    return file_obj


def required_doc_types_for_user():
    return [
        KycDocType.DRIVING_LICENSE_FRONT,
        KycDocType.DRIVING_LICENSE_BACK,
        KycDocType.SELFIE
    ]


def get_editable_kyc_case_for_user(user_id, db: Session):
    return db.query(KycCase)\
        .filter(KycCase.user_id == user_id)\
        .filter(KycCase.status.in_([KycStatus.KYC_IN_PROGRESS, KycStatus.KYC_NEEDS_ACTION]))\
        .order_by(KycCase.created_at.desc())\
        .first()


def ensure_case_editable(case: KycCase):
    if case.status not in [KycStatus.KYC_IN_PROGRESS, KycStatus.KYC_NEEDS_ACTION]:
        raise HTTPException(status_code=400, detail=f"KYC case not editable, current status: {case.status}")


def build_kyc_response(db: Session, user: User, case: Optional[KycCase]):
    if not case:
        return {
            "kyc_case_id": None,
            "case_status": "KYC_NOT_STARTED",
            "uploaded_doc_types": [],
            "missing_doc_types": [d.value for d in required_doc_types_for_user()],
            "can_submit": False,
            "documents": [],
            "next_action": "Start KYC"
        }

    required_docs = required_doc_types_for_user()
    uploaded_docs = [doc.doc_type for doc in case.documents]
    missing_docs = [d for d in required_docs if d not in uploaded_docs]
    can_submit = len(missing_docs) == 0

    docs_info = []
    for doc in case.documents:
        file_obj = db.query(FileObject).filter_by(id=doc.file_id).first()
        docs_info.append({
            "doc_type": doc.doc_type.value,
            "file_id": str(doc.file_id),
            "verified_bool": doc.verified_bool,
            "storage_uri": file_obj.storage_uri if file_obj else None,
            "file_name": file_obj.file_name if file_obj else None,
            "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None
        })

    next_action = "Upload missing documents" if missing_docs else "Submit KYC"

    return {
        "kyc_case_id": str(case.id),
        "case_status": case.status.value,
        "uploaded_doc_types": [d.value for d in uploaded_docs],
        "missing_doc_types": [d.value for d in missing_docs],
        "can_submit": can_submit,
        "documents": docs_info,
        "next_action": next_action
    }


# -----------------------------
# Pydantic schema for consents
# -----------------------------
class ConsentItem(BaseModel):
    consent_type: str
    status: str  # "Agree" or "Do not agree"


# -----------------------------
# User-side KYC Router
# -----------------------------
router = APIRouter(prefix="/user/kyc/status", tags=["KYC User"])


# -----------------------------
# Endpoints
# -----------------------------
@router.get("/", response_model=dict)
def get_user_kyc_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_editable_kyc_case_for_user(user.id, db)
    return build_kyc_response(db, user, case)


@router.post("/cases", response_model=dict)
def start_kyc_case(source: str = "user_app", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_editable_kyc_case_for_user(user.id, db)
    if case:
        return build_kyc_response(db, user, case)

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


@router.post("/consents", response_model=dict)
def upsert_user_consents(
    consents: List[ConsentItem],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    existing_consents = {c.consent_type: c for c in db.query(UserConsent).filter_by(user_id=user.id).all()}

    for consent in consents:
        try:
            consent_type_enum = ConsentType(consent.consent_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid consent_type: {consent.consent_type}")

        if consent.status == "Agree":
            status_enum = ConsentStatus.GRANTED
        elif consent.status == "Do not agree":
            status_enum = ConsentStatus.WITHDRAWN
        else:
            raise HTTPException(status_code=400, detail=f"Invalid consent status: {consent.status}")

        db_consent = existing_consents.get(consent_type_enum)

        if db_consent:
            db_consent.status = status_enum
            db_consent.granted_at = now if status_enum == ConsentStatus.GRANTED else None
            db_consent.withdrawn_at = now if status_enum == ConsentStatus.WITHDRAWN else None
        else:
            new_consent = UserConsent(
                user_id=user.id,
                consent_type=consent_type_enum,
                status=status_enum,
                granted_at=now if status_enum == ConsentStatus.GRANTED else None,
                withdrawn_at=now if status_enum == ConsentStatus.WITHDRAWN else None,
                version="1.0",
                source=ConsentSource.KYC_FLOW,
            )
            db.add(new_consent)

    db.commit()
    return {"message": "Consents updated successfully"}


# -----------------------------
# Bulk Upload Endpoint (fetch case from token, required + optional)
# -----------------------------
@router.patch("/documents/bulk", response_model=dict)
async def upload_bulk_kyc_documents(
    driving_license_expiry: date | None = Form(None),
    # Required files
    DRIVING_LICENSE_FRONT: UploadFile = File(...),
    DRIVING_LICENSE_BACK: UploadFile = File(...),
    AADHAAR_FRONT: UploadFile = File(...),
    AADHAAR_BACK: UploadFile = File(...),
    PAN: UploadFile = File(...),
    SELFIE: UploadFile = File(...),
    # Optional files
    PASSPORT: UploadFile | None = File(None),
    OTHER_ID: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Get editable KYC case from token automatically
    case = get_editable_kyc_case_for_user(user.id, db)
    if not case:
        raise HTTPException(status_code=404, detail="No editable KYC case found")
    ensure_case_editable(case)

    doc_map = {
        KycDocType.DRIVING_LICENSE_FRONT: DRIVING_LICENSE_FRONT,
        KycDocType.DRIVING_LICENSE_BACK: DRIVING_LICENSE_BACK,
        KycDocType.AADHAAR_FRONT: AADHAAR_FRONT,
        KycDocType.AADHAAR_BACK: AADHAAR_BACK,
        KycDocType.PAN: PAN,
        KycDocType.SELFIE: SELFIE,
        KycDocType.PASSPORT: PASSPORT,
        KycDocType.OTHER_ID: OTHER_ID
    }

    for doc_type_enum, upload_file in doc_map.items():
        if not upload_file:
            continue

        file_bytes = await upload_file.read()
        saved_path, metadata = save_file(file_bytes, upload_file.filename)
        checksum = hashlib.sha256(file_bytes).hexdigest()
        metadata.update({"checksum_sha256": checksum, "uploaded_by_user_id": str(user.id)})

        file_obj = db.query(FileObject).filter_by(checksum_sha256=checksum).first()
        if not file_obj:
            file_obj = create_or_get_file_object(
                db=db,
                storage_uri=saved_path,
                file_name=upload_file.filename,
                mime_type=upload_file.content_type,
                checksum_sha256=checksum,
                size_bytes=len(file_bytes),
                purpose=FilePurpose.KYC_SELFIE if doc_type_enum == KycDocType.SELFIE else FilePurpose.KYC_DOCUMENT,
                uploaded_by_user_id=user.id,
                metadata_json=metadata
            )

        expiry = driving_license_expiry if doc_type_enum in [KycDocType.DRIVING_LICENSE_FRONT, KycDocType.DRIVING_LICENSE_BACK] else None

        kyc_doc = db.query(KycDocument).filter_by(kyc_case_id=case.id, doc_type=doc_type_enum).first()
        if kyc_doc:
            kyc_doc.file_id = file_obj.id
            kyc_doc.expiry_date = expiry
            kyc_doc.verified_bool = False
            kyc_doc.document_number_masked = None
            kyc_doc.extracted_fields_json = {}
        else:
            kyc_doc = KycDocument(
                kyc_case_id=case.id,
                doc_type=doc_type_enum,
                file_id=file_obj.id,
                expiry_date=expiry,
                verified_bool=False,
                document_number_masked=None,
                extracted_fields_json={}
            )
            db.add(kyc_doc)

    if case.status == KycStatus.KYC_NEEDS_ACTION:
        case.status = KycStatus.KYC_IN_PROGRESS

    db.commit()
    return build_kyc_response(db, user, case)


# -----------------------------
# Delete document
# -----------------------------
@router.delete("/documents/{doc_type}", response_model=dict)
def delete_kyc_document(doc_type: KycDocType, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    case = get_editable_kyc_case_for_user(user.id, db)
    if not case:
        raise HTTPException(status_code=404, detail="No editable KYC case found")
    ensure_case_editable(case)

    kyc_doc = db.query(KycDocument).filter_by(kyc_case_id=case.id, doc_type=doc_type).first()
    if kyc_doc:
        db.delete(kyc_doc)
        db.commit()

    return build_kyc_response(db, user, case)


# -----------------------------
# Submit KYC
# -----------------------------
@router.post("/submit", response_model=dict)
def submit_kyc_case(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_editable_kyc_case_for_user(user.id, db)
    if not case:
        raise HTTPException(status_code=404, detail="No editable KYC case found")
    ensure_case_editable(case)

    required_docs = required_doc_types_for_user()
    existing_docs = {doc.doc_type for doc in case.documents}
    missing_docs = [d.value for d in required_docs if d not in existing_docs]
    if missing_docs:
        raise HTTPException(status_code=400, detail=f"Missing required documents: {missing_docs}")

    consents = db.query(UserConsent).filter_by(user_id=user.id).all()
    for consent in consents:
        if consent.status != ConsentStatus.GRANTED:
            raise HTTPException(status_code=400, detail=f"Consent {consent.consent_type.value} not granted.")

    case.status = KycStatus.KYC_SUBMITTED
    case.submitted_at = datetime.now(timezone.utc)
    user.kyc_status = KycStatus.KYC_SUBMITTED

    db.commit()
    db.refresh(case)
    return build_kyc_response(db, user, case)
# app/controllers/kyc/user_kyc_full.py

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
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

router = APIRouter(prefix="/user/kyc", tags=["KYC User"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "kyc_documents")


# -----------------------------
# HELPERS
# -----------------------------
def save_file(file_bytes: bytes, original_filename: str):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(original_filename)[1]
    filename = f"{py_uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as f:
        f.write(file_bytes)

    return path, {
        "original_file_name": original_filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }


def create_or_get_file_object(db: Session, **kwargs):
    existing = db.query(FileObject).filter_by(
        checksum_sha256=kwargs["checksum_sha256"]
    ).first()

    if existing:
        return existing

    obj = FileObject(**kwargs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def required_doc_types():
    return [
        KycDocType.DRIVING_LICENSE_FRONT,
        KycDocType.DRIVING_LICENSE_BACK,
        KycDocType.AADHAAR_FRONT,
        KycDocType.AADHAAR_BACK,
        KycDocType.PAN,
        KycDocType.SELFIE
    ]


def optional_doc_types():
    return [
        KycDocType.PASSPORT,
        KycDocType.OTHER_ID
    ]


def get_latest_case(user_id, db):
    return db.query(KycCase)\
        .filter(KycCase.user_id == user_id)\
        .order_by(KycCase.created_at.desc())\
        .first()


def get_editable_case(user_id, db):
    return db.query(KycCase)\
        .filter(KycCase.user_id == user_id)\
        .filter(KycCase.status.in_([
            KycStatus.KYC_IN_PROGRESS,
            KycStatus.KYC_NEEDS_ACTION
        ]))\
        .order_by(KycCase.created_at.desc())\
        .first()


def ensure_editable(case):
    if case.status not in [
        KycStatus.KYC_IN_PROGRESS,
        KycStatus.KYC_NEEDS_ACTION
    ]:
        raise HTTPException(400, f"Case not editable: {case.status}")


def check_kyc_processing_consent(db, user_id):
    consent = db.query(UserConsent).filter_by(
        user_id=user_id,
        consent_type=ConsentType.KYC_PROCESSING
    ).first()

    return consent and consent.status == ConsentStatus.GRANTED


# ✅ NEW HELPER (ONLY ADDITION)
def block_if_suspended(user: User):
    if user.kyc_status == KycStatus.KYC_SUSPENDED:
        raise HTTPException(403, "KYC is suspended. Contact support.")


# -----------------------------
# RESPONSE BUILDER
# -----------------------------
def build_response(db: Session, case: Optional[KycCase]):

    required = required_doc_types()
    optional = optional_doc_types()

    if not case:
        return {
            "kyc_case_id": None,
            "case_status": "KYC_NOT_STARTED",
            "uploaded_doc_types": [],
            "missing_doc_types": [d.value for d in required],
            "optional_doc_types": [d.value for d in optional],
            "can_submit": False,
            "documents": [],
            "next_action": "Start KYC"
        }

    uploaded = [d.doc_type for d in case.documents]
    uploaded_set = set(uploaded)

    missing = [d for d in required if d not in uploaded_set]
    can_submit = len(missing) == 0

    docs = []
    for doc in case.documents:
        file_obj = db.query(FileObject).filter_by(id=doc.file_id).first()

        docs.append({
            "kyc_document_id": str(doc.id),
            "doc_type": doc.doc_type.value,
            "verified_bool": doc.verified_bool,
            "file_name": file_obj.file_name if file_obj else None,
            "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None
        })

    if case.status == KycStatus.KYC_SUBMITTED:
        next_action = "Waiting for approval"
    elif case.status == KycStatus.KYC_REJECTED:
        next_action = "Re-upload rejected documents"
    elif missing:
        next_action = "Upload missing documents"
    else:
        next_action = "Submit KYC"

    return {
        "kyc_case_id": str(case.id),
        "case_status": case.status.value,
        "uploaded_doc_types": [d.value for d in uploaded],
        "missing_doc_types": [d.value for d in missing],
        "optional_doc_types": [d.value for d in optional],
        "can_submit": can_submit,
        "documents": docs,
        "next_action": next_action
    }


# -----------------------------
# 1️⃣ STATUS
# -----------------------------
@router.get("/status")
def get_cases(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_latest_case(user.id, db)
    return build_response(db, case)


# -----------------------------
# 2️⃣ START CASE
# -----------------------------
@router.post("/cases")
def start_case(db: Session = Depends(get_db), user: User = Depends(get_current_user)):

    block_if_suspended(user)  # ✅ FIX

    latest = get_latest_case(user.id, db)

    if latest and latest.status == KycStatus.KYC_SUBMITTED:
        return build_response(db, latest)

    existing = get_editable_case(user.id, db)
    if existing:
        return build_response(db, existing)

    case = KycCase(
        user_id=user.id,
        status=KycStatus.KYC_IN_PROGRESS,
        source="user_app"
    )

    db.add(case)

    if user.kyc_status == KycStatus.KYC_NOT_STARTED:
        user.kyc_status = KycStatus.KYC_IN_PROGRESS

    db.commit()
    db.refresh(case)

    return build_response(db, case)


# -----------------------------
# 3️⃣ CONSENTS
# -----------------------------
class ConsentItem(BaseModel):
    consent_type: str
    status: str


@router.post("/consents")
def consents(
    consents: List[ConsentItem],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    block_if_suspended(user)  # ✅ FIX

    now = datetime.now(timezone.utc)

    for c in consents:
        if c.consent_type != "KYC_PROCESSING":
            raise HTTPException(400, "Only KYC_PROCESSING consent is allowed")

        status_enum = (
            ConsentStatus.GRANTED if c.status == "Agree"
            else ConsentStatus.WITHDRAWN
        )

        db.merge(UserConsent(
            user_id=user.id,
            consent_type=ConsentType.KYC_PROCESSING,
            status=status_enum,
            granted_at=now if status_enum == ConsentStatus.GRANTED else None,
            withdrawn_at=now if status_enum == ConsentStatus.WITHDRAWN else None,
            source=ConsentSource.KYC_FLOW,
            version="1.0"
        ))

    db.commit()

    if not check_kyc_processing_consent(db, user.id):
        return {"message": "KYC consent not accepted"}

    latest = get_latest_case(user.id, db)

    if latest and latest.status == KycStatus.KYC_SUBMITTED:
        return build_response(db, latest)

    existing = get_editable_case(user.id, db)
    if existing:
        return {
            "message": "Updated consent",
            "existing_kyc_case": existing.id
        }

    case = KycCase(
        user_id=user.id,
        status=KycStatus.KYC_IN_PROGRESS,
        source="user_app"
    )

    db.add(case)

    if user.kyc_status == KycStatus.KYC_NOT_STARTED:
        user.kyc_status = KycStatus.KYC_IN_PROGRESS

    db.commit()
    db.refresh(case)

    return {
        "message": "KYC consent accepted",
        "initial_kyc_case_created": case.id
    }


# -----------------------------
# 4️⃣ UPLOAD DOCUMENTS
# -----------------------------
@router.patch("/documents/upload")
async def upload_docs(
    driving_license_expiry: date | None = Form(None),

    DRIVING_LICENSE_FRONT: UploadFile = File(None),
    DRIVING_LICENSE_BACK: UploadFile = File(None),
    AADHAAR_FRONT: UploadFile = File(None),
    AADHAAR_BACK: UploadFile = File(None),
    PAN: UploadFile = File(None),
    SELFIE: UploadFile = File(None),

    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    block_if_suspended(user)  # ✅ FIX

    case = get_latest_case(user.id, db)

    if case and case.status == KycStatus.KYC_SUBMITTED:
        raise HTTPException(400, "Cannot upload after submission")

    if not check_kyc_processing_consent(db, user.id):
        raise HTTPException(400, "Please accept KYC consent first")

    case = get_editable_case(user.id, db)
    if not case:
        raise HTTPException(404, "No editable case")

    ensure_editable(case)

    files = {
        KycDocType.DRIVING_LICENSE_FRONT: DRIVING_LICENSE_FRONT,
        KycDocType.DRIVING_LICENSE_BACK: DRIVING_LICENSE_BACK,
        KycDocType.AADHAAR_FRONT: AADHAAR_FRONT,
        KycDocType.AADHAAR_BACK: AADHAAR_BACK,
        KycDocType.PAN: PAN,
        KycDocType.SELFIE: SELFIE
    }

    any_uploaded = False

    for doc_type, file in files.items():
        if not file:
            continue

        any_uploaded = True

        file_bytes = await file.read()

        path, metadata = save_file(file_bytes, file.filename)
        checksum = hashlib.sha256(file_bytes).hexdigest()

        file_obj = create_or_get_file_object(
            db,
            storage_uri=path,
            file_name=file.filename,
            mime_type=file.content_type,
            checksum_sha256=checksum,
            size_bytes=len(file_bytes),
            purpose=FilePurpose.KYC_DOCUMENT,
            uploaded_by_user_id=user.id,
            metadata_json=metadata
        )

        expiry = driving_license_expiry if doc_type in [
            KycDocType.DRIVING_LICENSE_FRONT,
            KycDocType.DRIVING_LICENSE_BACK
        ] else None

        existing_doc = db.query(KycDocument).filter_by(
            kyc_case_id=case.id,
            doc_type=doc_type
        ).first()

        if existing_doc:
            existing_doc.file_id = file_obj.id
            existing_doc.verified_bool = False
            existing_doc.expiry_date = expiry
        else:
            db.add(KycDocument(
                kyc_case_id=case.id,
                doc_type=doc_type,
                file_id=file_obj.id,
                expiry_date=expiry,
                verified_bool=False
            ))

    if not any_uploaded:
        raise HTTPException(400, "No files provided")

    case.status = KycStatus.KYC_IN_PROGRESS

    db.commit()

    return build_response(db, case)


# -----------------------------
# 5️⃣ SUBMIT
# -----------------------------
@router.post("/submit")
def submit(db: Session = Depends(get_db), user: User = Depends(get_current_user)):

    block_if_suspended(user)  # ✅ FIX

    case = get_editable_case(user.id, db)
    if not case:
        raise HTTPException(404, "No editable case")

    required = required_doc_types()
    existing = {d.doc_type for d in case.documents}

    missing = [r for r in required if r not in existing]
    if missing:
        raise HTTPException(400, f"Missing documents: {[m.value for m in missing]}")

    if not check_kyc_processing_consent(db, user.id):
        raise HTTPException(400, "KYC consent not completed")

    case.status = KycStatus.KYC_SUBMITTED
    case.submitted_at = datetime.now(timezone.utc)
    user.kyc_status = KycStatus.KYC_SUBMITTED

    db.commit()

    return build_response(db, case)
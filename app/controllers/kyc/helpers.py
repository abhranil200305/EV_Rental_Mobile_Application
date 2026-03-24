# app/controllers/kyc/helpers.py

import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.schema import KycCase, KycDocument, FileObject, KycDocType, FilePurpose

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "kyc_documents")


# -----------------------------
# Required KYC doc types
# -----------------------------
def required_doc_types_for_user():
    # Example policy: driving license front/back + selfie required
    return [
        KycDocType.DRIVING_LICENSE_FRONT,
        KycDocType.DRIVING_LICENSE_BACK,
        KycDocType.SELFIE
    ]


# -----------------------------
# Build user-facing KYC response
# -----------------------------
def build_kyc_response(db: Session, user, case: KycCase | None):
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
    uploaded_docs = [doc.doc_type for doc in case.documents]  # ✅ Access KycDocument correctly

    missing_docs = [d for d in required_docs if d not in uploaded_docs]
    can_submit = len(missing_docs) == 0

    docs_info = []
    for doc in case.documents:  # ✅ Explicitly use KycDocument objects
        file_obj = db.query(FileObject).filter_by(id=doc.file_id).first()
        docs_info.append({
            "doc_type": doc.doc_type.value,
            "file_id": str(doc.file_id),
            "verified_bool": doc.verified_bool,
            "storage_uri": file_obj.storage_uri if file_obj else None,
            "file_name": file_obj.file_name if file_obj else None
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
# Create or reuse a FileObject row
# -----------------------------
def create_or_get_file_object(
    db: Session,
    storage_uri: str,
    file_name: str,
    mime_type: str,
    checksum_sha256: str,
    size_bytes: int,
    purpose: FilePurpose,
    uploaded_by_user_id: uuid.UUID,
    metadata_json: dict
):
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


# -----------------------------
# Save file locally
# -----------------------------
def save_file(file_bytes: bytes, original_filename: str):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(original_filename)[1]
    server_filename = f"{uuid.uuid4().hex}{ext}"
    storage_path = os.path.join(UPLOAD_DIR, server_filename)

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    metadata = {"original_file_name": original_filename, "uploaded_at": datetime.utcnow().isoformat()}
    return storage_path, metadata
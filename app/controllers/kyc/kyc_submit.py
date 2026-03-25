# app/controllers/kyc/kyc_submit.py
'''
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schema import KycCase, KycDocument, KycDocType, KycStatus
from app.services.file_service import create_file_object
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/kyc/upload-document")
def upload_kyc_document(
    doc_type: KycDocType,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # -----------------------------
    # 0️⃣ Basic validation
    # -----------------------------
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    # -----------------------------
    # 1️⃣ Get latest KYC case
    # -----------------------------
    kyc_case = (
        db.query(KycCase)
        .filter(KycCase.user_id == user.id)
        .order_by(KycCase.created_at.desc())
        .first()
    )

    # -----------------------------
    # 2️⃣ Create new case if none exists
    # -----------------------------
    if not kyc_case:
        kyc_case = KycCase(
            user_id=user.id,
            status=KycStatus.KYC_IN_PROGRESS
        )
        db.add(kyc_case)
        db.commit()
        db.refresh(kyc_case)

    # -----------------------------
    # 3️⃣ Prevent upload if already approved
    # -----------------------------
    if kyc_case.status == KycStatus.KYC_APPROVED:
        raise HTTPException(
            status_code=400,
            detail="KYC already approved. Cannot upload new documents."
        )

    # -----------------------------
    # 4️⃣ Save file → file_objects
    # -----------------------------
    try:
        file_obj = create_file_object(db, file, user.id)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="File upload failed"
        )

    # -----------------------------
    # 5️⃣ Create / replace KYC document
    # -----------------------------
    existing_doc = (
        db.query(KycDocument)
        .filter(
            KycDocument.kyc_case_id == kyc_case.id,
            KycDocument.doc_type == doc_type
        )
        .first()
    )

    if existing_doc:
        existing_doc.file_id = file_obj.id
        existing_doc.verified_bool = False  # reset verification
    else:
        new_doc = KycDocument(
            kyc_case_id=kyc_case.id,
            doc_type=doc_type,
            file_id=file_obj.id,
            verified_bool=False
        )
        db.add(new_doc)

    # -----------------------------
    # 6️⃣ Update case status (important flow)
    # -----------------------------
    if kyc_case.status in [
        KycStatus.KYC_REJECTED,
        KycStatus.KYC_NEEDS_ACTION
    ]:
        kyc_case.status = KycStatus.KYC_IN_PROGRESS

    # -----------------------------
    # 7️⃣ Commit all changes
    # -----------------------------
    db.commit()

    # -----------------------------
    # 8️⃣ Response
    # -----------------------------
    return {
        "message": "Document uploaded successfully",
        "kyc_case_id": str(kyc_case.id),
        "file_id": str(file_obj.id)
    }
'''
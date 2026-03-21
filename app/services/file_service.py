from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.db.schema import FileObject
from app.core.config import STORAGE_TYPE
from app.services.storage.local_storage import save_file_local
from app.services.storage.s3_storage import save_file_s3  # placeholder, safe import

# Allowed MIME types for KYC documents
ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]


def save_file(file, db: Session):
    """
    Save uploaded file to storage (local or S3) and insert a FileObject record in DB.

    Currently:
        - Uses local storage for all uploads.
        - S3 will be used later when AWS is configured.

    Returns:
        FileObject instance
    """
    # Validate MIME type
    if file.content_type not in ALLOWED_TYPES:
        raise Exception("Only JPG, PNG, PDF allowed")

    # Decide storage based on STORAGE_TYPE
    if STORAGE_TYPE.upper() == "S3":
        # Safe to import, will raise NotImplementedError until S3 is configured
        try:
            storage_uri, mime = save_file_s3(file)
        except NotImplementedError:
            # Fallback to local storage until S3 is configured
            storage_uri, mime = save_file_local(file)
    else:
        storage_uri, mime = save_file_local(file)

    # Insert FileObject record in DB
    file_obj = FileObject(
        id=uuid.uuid4(),
        storage_uri=storage_uri,
        mime=mime,
        checksum=None,  # Optional: add checksum logic if needed
        created_at=datetime.utcnow()
    )
    db.add(file_obj)
    db.flush()  # Ensure file_obj.id is available immediately

    return file_obj
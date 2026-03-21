import os
import uuid
from fastapi import UploadFile
from app.core.config import UPLOAD_DIR

# Ensure the upload folder exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_file_local(file: UploadFile):
    """
    Save uploaded file to local Documents_upload folder.
    Returns: (file_path, mime_type)
    """
    # Generate a unique filename
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1].lower()
    filename = f"{file_id}.{ext}"

    file_path = os.path.join(UPLOAD_DIR, filename)

    # Write file
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path, file.content_type
# app/services/storage/s3_storage.py

import boto3
import uuid
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from app.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET_NAME
)


# -----------------------------
# Create S3 client
# -----------------------------
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


def save_file_s3(file_bytes: bytes, filename: str) -> str:
    """
    Upload file to AWS S3 and return public URL or object key.

    Parameters:
    - file_bytes: file content
    - filename: original filename

    Returns:
    - storage_uri (str)
    """

    # -----------------------------
    # Generate unique filename
    # -----------------------------
    ext = filename.split(".")[-1] if "." in filename else "bin"
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    # Example folder structure in S3
    s3_key = f"uploads/documents/{unique_name}"

    # -----------------------------
    # Upload to S3
    # -----------------------------
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType="application/octet-stream"
        )

    except (BotoCoreError, ClientError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to S3"
        )

    # -----------------------------
    # Return file URL (or key)
    # -----------------------------
    file_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

    return file_url
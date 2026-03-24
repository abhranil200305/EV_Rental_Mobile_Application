
# app/core/config.py

import os
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

# -----------------------------
# Base directory of the project
# -----------------------------
# EV_Rental_Mobile_Application/
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

# -----------------------------
# File storage configuration
# -----------------------------
# Local storage folder (relative to BASE_DIR)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "Documents_upload")

# Ensure upload directory exists (IMPORTANT)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Storage type: LOCAL or S3
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "LOCAL").upper()

# Validate storage type
if STORAGE_TYPE not in ["LOCAL", "S3"]:
    raise ValueError("Invalid STORAGE_TYPE. Must be either 'LOCAL' or 'S3'")

# -----------------------------
# Optional AWS S3 config (future)
# -----------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "your-bucket-name")

# -----------------------------
# Other configs (future use)
# -----------------------------
# Example:
# JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
# RAZORPAY_KEY = os.getenv("RAZORPAY_KEY", "")

# -----------------------------
# Debug (optional - remove in production)
# -----------------------------
# print("BASE_DIR:", BASE_DIR)
# print("UPLOAD_DIR:", UPLOAD_DIR)
# print("STORAGE_TYPE:", STORAGE_TYPE)


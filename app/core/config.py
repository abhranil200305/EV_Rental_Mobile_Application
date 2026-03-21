import os
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()

# -----------------------------
# Base directory of the project
# -----------------------------
# EV_Rental_Mobile_Application/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -----------------------------
# File storage configuration
# -----------------------------
# Local storage folder (relative to BASE_DIR)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "Documents_upload")

# Storage type: LOCAL or S3
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "LOCAL").upper()

# -----------------------------
# Optional AWS S3 config (future)
# -----------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "your-bucket-name")

# -----------------------------
# Other configs can go here
# -----------------------------
# e.g., JWT_SECRET, RAZORPAY_KEY, etc.
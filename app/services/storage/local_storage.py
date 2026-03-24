# app/services/storage/local_storage.py

import os
import uuid
from pathlib import Path
from app.core.config import UPLOAD_DIR


def save_file(file_bytes: bytes, filename: str) -> str:
    """
    Save file locally and return file path.

    Parameters:
    - file_bytes: file content in bytes
    - filename: original filename (used only for extension)

    Returns:
    - file_path (str): stored file path (Windows style)
    """

    # -----------------------------
    # 1️⃣ Ensure upload directory exists
    # -----------------------------
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # -----------------------------
    # 2️⃣ Extract extension safely
    # -----------------------------
    ext = Path(filename).suffix.lower()
    if not ext:
        ext = ".bin"

    # -----------------------------
    # 3️⃣ Generate unique filename
    # -----------------------------
    unique_name = f"{uuid.uuid4()}{ext}"

    # -----------------------------
    # 4️⃣ Use direct folder (NO SHARDING)
    # -----------------------------
    final_dir = UPLOAD_DIR
    os.makedirs(final_dir, exist_ok=True)

    # -----------------------------
    # 5️⃣ Full file path
    # -----------------------------
    file_path = os.path.join(final_dir, unique_name)

    # -----------------------------
    # 6️⃣ Write file
    # -----------------------------
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # -----------------------------
    # 7️⃣ Force Windows-style path
    # -----------------------------
    file_path = file_path.replace("/", "\\")

    return file_path
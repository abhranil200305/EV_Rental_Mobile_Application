# app/utils/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
import os
import uuid

from app.db.database import get_db
from app.db.schema import User, UserStatus
from dotenv import load_dotenv

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

# -------------------------
# OAuth2 scheme
# -------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# -------------------------
# JWT config
# -------------------------
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set in .env")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


# -------------------------
# Get Current User
# -------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("user_id") or payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Convert to UUID (IMPORTANT FIX)
        user_id = uuid.UUID(user_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # -------------------------
    # Fetch user from DB
    # -------------------------
    user = db.query(User).filter(
        User.id == user_id,
        User.status != UserStatus.DELETED
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # -------------------------
    # Ensure user is ACTIVE (IMPORTANT FIX)
    # -------------------------
    if user.status not in [UserStatus.ACTIVE, UserStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not active"
        )

    return user

from app.db.schema import UserType

def get_current_admin(
    user: User = Depends(get_current_user)
) -> User:
    if user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user
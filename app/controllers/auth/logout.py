# app/controllers/auth/logout.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import jwt
import os
import uuid

from app.db.database import get_db
from app.db.schema import Session as UserSession, SessionStatus
from app.utils.auth import get_current_user, oauth2_scheme

router = APIRouter(prefix="/auth", tags=["Auth"])

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Logout the current user by revoking only the current session/token.
    """

    # Decode JWT
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Extract jti
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=400, detail="Token missing jti")

    # Convert to UUID
    try:
        session_id = uuid.UUID(jti)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id in token")

    # Fetch session
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session already inactive")

    # Revoke session
    now = datetime.now(timezone.utc)
    session.status = SessionStatus.REVOKED
    session.revoked_at = now
    session.last_seen_at = now

    db.commit()

    return {
        "message": "Logged out successfully"
    }
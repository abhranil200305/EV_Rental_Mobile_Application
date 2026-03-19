# app/utils/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
import os
from app.db.database import get_db
from app.db.schema import User
from dotenv import load_dotenv

# Load .env variables
load_dotenv()  # looks for .env in the project root

# FastAPI OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# JWT config from .env
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set in .env")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # default to HS256

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Fetch user from DB
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user
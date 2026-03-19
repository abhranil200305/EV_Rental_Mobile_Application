# app/schemas/admin_schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from app.db.schema import UserType, UserStatus, KycStatus

# -------------------------
# Request Schema
# -------------------------
class UserBatchRequest(BaseModel):
    admin_user_id: UUID
    user_ids: List[UUID]
    page: int = 1
    page_size: int = 10

# -------------------------
# Response Schemas
# -------------------------
class UserDetail(BaseModel):
    id: UUID
    phone_e164: Optional[str]   # optional now
    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    user_type: UserType
    status: UserStatus
    kyc_status: KycStatus
    date_of_birth: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class TotalUsers(BaseModel):
    available_users: int
    not_found_users: int

class UserListResponse(BaseModel):
    users: List[UserDetail]
    not_found_ids: List[str]
    page: int
    page_size: int
    total_users: TotalUsers  # <-- changed from int to TotalUsers
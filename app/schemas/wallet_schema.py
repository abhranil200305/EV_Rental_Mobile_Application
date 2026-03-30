# app/schemas/wallet_schema.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from app.db.schema import WalletEntryDirection, WalletEntryType


# =========================================
# 📦 REQUEST SCHEMAS
# =========================================

class CreateWalletRechargeRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount in INR")


class VerifyWalletRechargeRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


# =========================================
# 📤 RESPONSE SCHEMAS
# =========================================

class CreateWalletRechargeResponse(BaseModel):
    order_id: str
    amount: Decimal
    currency: str = "INR"


class WalletBalanceResponse(BaseModel):
    available_balance: Decimal
    reserved_balance: Decimal
    due_balance: Decimal
    currency: str = "INR"


# =========================================
# 📜 WALLET LEDGER / TRANSACTION
# =========================================

class WalletTransactionResponse(BaseModel):
    id: UUID
    created_at: datetime   # renamed from 'ts' → matches DB

    direction: WalletEntryDirection
    entry_type: WalletEntryType

    amount: Decimal
    balance_after: Optional[Decimal]

    reference: Optional[str]
    currency: str = "INR"

    class Config:
        from_attributes = True


# =========================================
# 📜 LIST TRANSACTIONS RESPONSE (PAGINATED)
# =========================================

class WalletTransactionListResponse(BaseModel):
    transactions: List[WalletTransactionResponse]
    total: int
    limit: int
    offset: int


# =========================================
# ✅ GENERIC MESSAGE RESPONSE
# =========================================

class MessageResponse(BaseModel):
    message: str
    status: str = "success"
    balance: Optional[Decimal] = None
#app/conterollers/wallet/wallet_controllers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import logging
from decimal import Decimal
from datetime import datetime, timezone

from app.db.database import get_db
from app.db.schema import (
    WalletAccount,
    PaymentIntent,
    Payment,
    WalletLedgerEntry,
    PaymentProvider,
    PaymentPurpose,
    PaymentStatus,
    WalletEntryDirection,
    WalletEntryType,
    User
)

from app.controllers.payments.razorpay_service import (
    create_razorpay_order,
    verify_razorpay_signature
)

from app.utils.auth import get_current_user


router = APIRouter(prefix="/wallet", tags=["Wallet"])
logger = logging.getLogger(__name__)


# ============================
# 📦 REQUEST SCHEMAS
# ============================

class CreateOrderRequest(BaseModel):
    amount: float


class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


# ============================
# 🧠 HELPER FUNCTION
# ============================

def get_or_create_wallet(db: Session, user_id: uuid.UUID) -> WalletAccount:
    wallet = db.query(WalletAccount).filter_by(user_id=user_id).first()

    if not wallet:
        wallet = WalletAccount(
            user_id=user_id,
            currency_code="INR",
            available_balance_minor=0,
            reserved_balance_minor=0,
            due_balance_minor=0
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    return wallet


# ============================
# 💰 CREATE RECHARGE 
# ============================

@router.post("/recharge/addbalance")
def create_wallet_recharge_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")

        # ✅ FIX: Decimal precision
        amount_minor = int(Decimal(str(request.amount)) * 100)

        idempotency_key = str(uuid.uuid4())

        # Create PaymentIntent
        payment_intent = PaymentIntent(
            user_id=current_user.id,
            provider=PaymentProvider.RAZORPAY,
            purpose=PaymentPurpose.WALLET_TOPUP,
            amount_minor=amount_minor,
            currency_code="INR",
            status=PaymentStatus.CREATED,
            idempotency_key=idempotency_key
        )

        db.add(payment_intent)
        db.commit()
        db.refresh(payment_intent)

        # Create Razorpay order
        razorpay_order = create_razorpay_order(amount_minor)

        # Update intent
        payment_intent.provider_order_ref = razorpay_order["id"]
        payment_intent.status = PaymentStatus.PENDING

        db.commit()

        return {
            "order_id": razorpay_order["id"],
            "amount": request.amount,
            "currency": "INR"
        }

    except Exception as e:
        logger.error(f"Create order failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create order")


# ============================
# 🔐 VERIFY PAYMENT & CREDIT WALLET
# ============================

@router.post("/recharge/verify")
def verify_wallet_recharge(
    request: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # -----------------------------
        # 1. VERIFY SIGNATURE
        # -----------------------------
        is_valid = verify_razorpay_signature(
            request.razorpay_order_id,
            request.razorpay_payment_id,
            request.razorpay_signature
        )

        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        # -----------------------------
        # 2. FETCH PAYMENT INTENT
        # -----------------------------
        intent = db.query(PaymentIntent).filter_by(
            provider_order_ref=request.razorpay_order_id,
            user_id=current_user.id
        ).first()

        if not intent:
            raise HTTPException(status_code=404, detail="Payment intent not found")

        wallet = get_or_create_wallet(db, current_user.id)

        # -----------------------------
        # 3. IDEMPOTENCY CHECK (CRITICAL)
        # -----------------------------
        if intent.status == PaymentStatus.CAPTURED:
            return {
                "message": "Payment already processed",
                "balance": wallet.available_balance_minor / 100
            }

        existing_payment = db.query(Payment).filter_by(
            provider_payment_ref=request.razorpay_payment_id
        ).first()

        if existing_payment:
            return {
                "message": "Payment already processed",
                "balance": wallet.available_balance_minor / 100
            }

        # -----------------------------
        # 4. CREATE PAYMENT RECORD
        # -----------------------------
        payment = Payment(
            user_id=current_user.id,
            payment_intent_id=intent.id,
            provider=PaymentProvider.RAZORPAY,
            purpose=PaymentPurpose.WALLET_TOPUP,
            status=PaymentStatus.CAPTURED,
            provider_payment_ref=request.razorpay_payment_id,
            provider_order_ref=request.razorpay_order_id,
            amount_minor=intent.amount_minor,
            currency_code="INR",
            captured_at=datetime.now(timezone.utc)
        )

        db.add(payment)
        db.flush()

        # -----------------------------
        # 5. CREDIT WALLET (LEDGER FIRST)
        # -----------------------------
        new_balance = wallet.available_balance_minor + intent.amount_minor

        ledger_entry = WalletLedgerEntry(
            wallet_account_id=wallet.id,
            direction=WalletEntryDirection.CREDIT,
            entry_type=WalletEntryType.TOPUP,
            amount_minor=intent.amount_minor,
            balance_after_minor=new_balance,
            payment_id=payment.id,
            reference=request.razorpay_order_id
        )

        db.add(ledger_entry)

        # update wallet snapshot AFTER ledger
        wallet.available_balance_minor = new_balance

        # -----------------------------
        # 6. UPDATE INTENT STATUS
        # -----------------------------
        intent.status = PaymentStatus.CAPTURED

        # -----------------------------
        # 7. COMMIT
        # -----------------------------
        db.commit()

        return {
            "message": "Wallet recharged successfully",
            "balance": new_balance / 100
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify payment failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Payment verification failed")


# ============================
# 💳 GET WALLET BALANCE
# ============================

@router.get("/balance")
def get_wallet_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallet = get_or_create_wallet(db, current_user.id)

    return {
        "available_balance": wallet.available_balance_minor / 100,
        "reserved_balance": wallet.reserved_balance_minor / 100,
        "due_balance": wallet.due_balance_minor / 100
    }
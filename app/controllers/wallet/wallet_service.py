#app/controllers/wallet/wallet_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

from app.db.schema import (
    WalletAccount,
    WalletLedgerEntry,
    PaymentIntent,
    Payment,
    PaymentProvider,
    PaymentPurpose,
    PaymentStatus,
    WalletEntryDirection,
    WalletEntryType
)

from app.controllers.payments.razorpay_service import (
    create_razorpay_order,
    verify_razorpay_signature
)


# =========================================
# 🧠 WALLET HELPER
# =========================================

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


# =========================================
# 💰 CREATE PAYMENT INTENT + ORDER
# =========================================

def create_wallet_topup_order(
    db: Session,
    user_id: uuid.UUID,
    amount: float
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    amount_minor = int(amount * 100)

    idempotency_key = str(uuid.uuid4())

    # Create PaymentIntent
    payment_intent = PaymentIntent(
        user_id=user_id,
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

    # Create Razorpay Order
    razorpay_order = create_razorpay_order(amount_minor)

    # Update intent
    payment_intent.provider_order_ref = razorpay_order["id"]
    payment_intent.status = PaymentStatus.PENDING

    db.commit()

    return {
        "order_id": razorpay_order["id"],
        "amount": amount,
        "currency": "INR"
    }


# =========================================
# 🔐 VERIFY PAYMENT + CREDIT WALLET
# =========================================

def verify_wallet_topup(
    db: Session,
    user_id: uuid.UUID,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
):
    # -----------------------------
    # 1. VERIFY SIGNATURE
    # -----------------------------
    is_valid = verify_razorpay_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # -----------------------------
    # 2. FETCH PAYMENT INTENT
    # -----------------------------
    intent = db.query(PaymentIntent).filter_by(
        provider_order_ref=razorpay_order_id,
        user_id=user_id
    ).first()

    if not intent:
        raise HTTPException(status_code=404, detail="Payment intent not found")

    # -----------------------------
    # 3. IDEMPOTENCY CHECK
    # -----------------------------
    existing_payment = db.query(Payment).filter_by(
        provider_payment_ref=razorpay_payment_id
    ).first()

    if existing_payment:
        return {
            "message": "Payment already processed",
            "balance": get_wallet_balance(db, user_id)
        }

    # -----------------------------
    # 4. CREATE PAYMENT RECORD
    # -----------------------------
    payment = Payment(
        user_id=user_id,
        payment_intent_id=intent.id,
        provider=PaymentProvider.RAZORPAY,
        purpose=PaymentPurpose.WALLET_TOPUP,
        status=PaymentStatus.CAPTURED,
        provider_payment_ref=razorpay_payment_id,
        provider_order_ref=razorpay_order_id,
        amount_minor=intent.amount_minor,
        currency_code="INR"
    )

    db.add(payment)
    db.flush()  # get payment.id

    # -----------------------------
    # 5. CREDIT WALLET (LEDGER FIRST)
    # -----------------------------
    wallet = get_or_create_wallet(db, user_id)

    new_balance = wallet.available_balance_minor + intent.amount_minor

    ledger_entry = WalletLedgerEntry(
        wallet_account_id=wallet.id,
        direction=WalletEntryDirection.CREDIT,
        entry_type=WalletEntryType.TOPUP,
        amount_minor=intent.amount_minor,
        balance_after_minor=new_balance,
        payment_id=payment.id,
        reference=razorpay_order_id
    )

    db.add(ledger_entry)

    # update wallet snapshot
    wallet.available_balance_minor = new_balance

    # -----------------------------
    # 6. UPDATE PAYMENT INTENT
    # -----------------------------
    intent.status = PaymentStatus.CAPTURED

    # -----------------------------
    # 7. COMMIT TRANSACTION
    # -----------------------------
    db.commit()

    return {
        "message": "Wallet recharged successfully",
        "balance": new_balance / 100
    }


# =========================================
# 💳 GET WALLET BALANCE
# =========================================

def get_wallet_balance(db: Session, user_id: uuid.UUID):
    wallet = get_or_create_wallet(db, user_id)

    return {
        "available_balance": wallet.available_balance_minor / 100,
        "reserved_balance": wallet.reserved_balance_minor / 100,
        "due_balance": wallet.due_balance_minor / 100
    }
# app/controllers/payments/razorpay_service.py

import razorpay
import os
import hmac
import hashlib
import logging
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# =========================================
# 🔐 LOAD ENV FILE (SAFE)
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load only if not already loaded
load_dotenv(dotenv_path=ENV_PATH, override=False)


# =========================================
# 🔐 ENV VARIABLES
# =========================================

RAZORPAY_KEY = os.getenv("RAZOR_PAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZOR_PAY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")


# ⚠️ DO NOT CRASH APP ON IMPORT
if not RAZORPAY_KEY or not RAZORPAY_SECRET:
    logger.warning("⚠️ Razorpay credentials not loaded. Payment APIs may fail.")


# =========================================
# 🧠 LAZY CLIENT (BEST PRACTICE)
# =========================================

def get_razorpay_client():
    """
    Create Razorpay client only when needed
    """
    if not RAZORPAY_KEY or not RAZORPAY_SECRET:
        raise Exception("Razorpay credentials not configured properly")

    return razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))


# =========================================
# 💰 CREATE ORDER
# =========================================

def create_razorpay_order(amount_minor: int) -> Dict:
    """
    Create Razorpay order
    amount_minor = amount in paisa
    """
    try:
        client = get_razorpay_client()

        order = client.order.create({
            "amount": amount_minor,
            "currency": "INR",
            "payment_capture": 1
        })

        return order

    except Exception as e:
        logger.error(f"❌ Razorpay order creation failed: {str(e)}")
        raise Exception("Failed to create Razorpay order")


# =========================================
# 🔐 VERIFY SIGNATURE (Frontend Flow)
# =========================================

def verify_razorpay_signature(
    order_id: str,
    payment_id: str,
    signature: str
) -> bool:
    try:
        if not RAZORPAY_SECRET:
            logger.error("❌ Razorpay secret not configured")
            return False

        body = f"{order_id}|{payment_id}"

        generated_signature = hmac.new(
            RAZORPAY_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(generated_signature, signature)

    except Exception as e:
        logger.error(f"❌ Signature verification failed: {str(e)}")
        return False


# =========================================
# 🔔 VERIFY WEBHOOK SIGNATURE
# =========================================

def verify_webhook_signature(
    body: bytes,
    signature: str
) -> bool:
    try:
        if not RAZORPAY_WEBHOOK_SECRET:
            logger.error("❌ Webhook secret not configured")
            return False

        generated_signature = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(generated_signature, signature)

    except Exception as e:
        logger.error(f"❌ Webhook signature verification failed: {str(e)}")
        return False


# =========================================
# 📦 FETCH PAYMENT
# =========================================

def fetch_payment(payment_id: str) -> Dict:
    try:
        client = get_razorpay_client()
        return client.payment.fetch(payment_id)

    except Exception as e:
        logger.error(f"❌ Fetch payment failed: {str(e)}")
        raise Exception("Failed to fetch payment")


# =========================================
# 🔁 FETCH ORDER
# =========================================

def fetch_order(order_id: str) -> Dict:
    try:
        client = get_razorpay_client()
        return client.order.fetch(order_id)

    except Exception as e:
        logger.error(f"❌ Fetch order failed: {str(e)}")
        raise Exception("Failed to fetch order")
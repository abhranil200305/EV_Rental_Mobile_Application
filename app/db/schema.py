
from __future__ import annotations

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ============================================================================
# Base
# ============================================================================


class Base(DeclarativeBase):
    pass


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# ============================================================================
# Enums
# ============================================================================


class UserType(str, enum.Enum):
    DRIVER = "DRIVER"
    ADMIN = "ADMIN"
    SUPPORT = "SUPPORT"
    FINANCE = "FINANCE"
    FLEET_OPS = "FLEET_OPS"
    SUPERADMIN = "SUPERADMIN"


class UserStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BLACKLISTED = "BLACKLISTED"
    DELETED = "DELETED"


class UserSuspendedReason(str, enum.Enum):
    KYC_PENDING_REVIEW = "KYC_PENDING_REVIEW"
    KYC_NEEDS_REUPLOAD = "KYC_NEEDS_REUPLOAD"
    KYC_EXPIRED = "KYC_EXPIRED"
    PAYMENT_DUE = "PAYMENT_DUE"
    PAYMENT_DISPUTE = "PAYMENT_DISPUTE"
    DAMAGE_UNDER_REVIEW = "DAMAGE_UNDER_REVIEW"
    DAMAGE_PENDING_RECOVERY = "DAMAGE_PENDING_RECOVERY"
    RISK_REVIEW = "RISK_REVIEW"
    SAFETY_REVIEW = "SAFETY_REVIEW"
    GEOFENCE_VIOLATION_REVIEW = "GEOFENCE_VIOLATION_REVIEW"
    SUPPORT_ESCALATION_HOLD = "SUPPORT_ESCALATION_HOLD"
    ADMIN_TEMP_BLOCK = "ADMIN_TEMP_BLOCK"
    LEGAL_HOLD = "LEGAL_HOLD"
    OTHER = "OTHER"


class UserBlacklistedReason(str, enum.Enum):
    FRAUD_CONFIRMED = "FRAUD_CONFIRMED"
    MULTIPLE_ACCOUNT_ABUSE = "MULTIPLE_ACCOUNT_ABUSE"
    PAYMENT_ABUSE = "PAYMENT_ABUSE"
    CHARGEBACK_ABUSE = "CHARGEBACK_ABUSE"
    SERIOUS_DAMAGE_LIABILITY = "SERIOUS_DAMAGE_LIABILITY"
    VEHICLE_THEFT_RISK = "VEHICLE_THEFT_RISK"
    DOCUMENT_FORGERY = "DOCUMENT_FORGERY"
    IDENTITY_MISMATCH_CONFIRMED = "IDENTITY_MISMATCH_CONFIRMED"
    REPEATED_SAFETY_VIOLATIONS = "REPEATED_SAFETY_VIOLATIONS"
    REPEATED_GEOFENCE_ABUSE = "REPEATED_GEOFENCE_ABUSE"
    REPEATED_POLICY_VIOLATION = "REPEATED_POLICY_VIOLATION"
    LEGAL_OR_POLICE_DIRECTION = "LEGAL_OR_POLICE_DIRECTION"
    ADMIN_PERMANENT_BLOCK = "ADMIN_PERMANENT_BLOCK"
    OTHER = "OTHER"

class ConsentSource(str, enum.Enum):
    SIGNUP_FLOW = "SIGNUP_FLOW"
    LOGIN_FLOW = "LOGIN_FLOW"
    PROFILE_SETTINGS = "PROFILE_SETTINGS"
    BOOKING_FLOW = "BOOKING_FLOW"
    KYC_FLOW = "KYC_FLOW"
    CHECKOUT_FLOW = "CHECKOUT_FLOW"
    APP_POPUP = "APP_POPUP"
    WEB_PORTAL = "WEB_PORTAL"
    ADMIN_PANEL = "ADMIN_PANEL"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    SYSTEM_MIGRATION = "SYSTEM_MIGRATION"
    BACKFILL = "BACKFILL"
    API = "API"
    UNKNOWN = "UNKNOWN"

class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class DevicePlatform(str, enum.Enum):
    ANDROID = "ANDROID"
    IOS = "IOS"
    WEB = "WEB"
    UNKNOWN = "UNKNOWN"


class OtpPurpose(str, enum.Enum):
    LOGIN = "LOGIN"
    SIGNUP = "SIGNUP"
    DEVICE_CHANGE = "DEVICE_CHANGE"
    SENSITIVE_ACTION = "SENSITIVE_ACTION"


class OtpStatus(str, enum.Enum):
    ISSUED = "ISSUED"
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"
    LOCKED = "LOCKED"
    CANCELLED = "CANCELLED"


class ConsentType(str, enum.Enum):
    PRIVACY_NOTICE = "PRIVACY_NOTICE"
    TERMS_AND_CONDITIONS = "TERMS_AND_CONDITIONS"
    LOCATION_TRACKING = "LOCATION_TRACKING"
    KYC_PROCESSING = "KYC_PROCESSING"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    MARKETING = "MARKETING"


class ConsentStatus(str, enum.Enum):
    GRANTED = "GRANTED"
    WITHDRAWN = "WITHDRAWN"


class FilePurpose(str, enum.Enum):
    KYC_DOCUMENT = "KYC_DOCUMENT"
    KYC_SELFIE = "KYC_SELFIE"
    TRIP_PRE_PHOTO = "TRIP_PRE_PHOTO"
    TRIP_POST_PHOTO = "TRIP_POST_PHOTO"
    INCIDENT_EVIDENCE = "INCIDENT_EVIDENCE"
    DAMAGE_EVIDENCE = "DAMAGE_EVIDENCE"
    CLAIM_DOCUMENT = "CLAIM_DOCUMENT"
    MAINTENANCE_DOCUMENT = "MAINTENANCE_DOCUMENT"
    SUPPORT_ATTACHMENT = "SUPPORT_ATTACHMENT"
    INVOICE_PDF = "INVOICE_PDF"
    VEHICLE_DOCUMENT = "VEHICLE_DOCUMENT"
    OTHER = "OTHER"

class KycStatus(str, enum.Enum):
    KYC_NOT_STARTED = "KYC_NOT_STARTED"
    KYC_IN_PROGRESS = "KYC_IN_PROGRESS"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_NEEDS_ACTION = "KYC_NEEDS_ACTION"
    KYC_APPROVED = "KYC_APPROVED"
    KYC_REJECTED = "KYC_REJECTED"
    KYC_SUSPENDED = "KYC_SUSPENDED"


class KycDocType(str, enum.Enum):
    DRIVING_LICENSE_FRONT = "DRIVING_LICENSE_FRONT"
    DRIVING_LICENSE_BACK = "DRIVING_LICENSE_BACK"
    AADHAAR_FRONT = "AADHAAR_FRONT"
    AADHAAR_BACK = "AADHAAR_BACK"
    PAN = "PAN"
    SELFIE = "SELFIE"
    PASSPORT = "PASSPORT"
    OTHER_ID = "OTHER_ID"


class KycRejectReasonCode(str, enum.Enum):
    BLURRY_DOCUMENT = "BLURRY_DOCUMENT"
    EXPIRED_DOCUMENT = "EXPIRED_DOCUMENT"
    NAME_MISMATCH = "NAME_MISMATCH"
    DOB_MISMATCH = "DOB_MISMATCH"
    FACE_MISMATCH = "FACE_MISMATCH"
    DOCUMENT_UNREADABLE = "DOCUMENT_UNREADABLE"
    INVALID_DRIVING_LICENSE = "INVALID_DRIVING_LICENSE"
    DUPLICATE_ACCOUNT = "DUPLICATE_ACCOUNT"
    FRAUD_SUSPECTED = "FRAUD_SUSPECTED"
    MANUAL_POLICY_REJECTION = "MANUAL_POLICY_REJECTION"
    OTHER = "OTHER"


class VehicleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"

class ChargingStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    NOT_CHARGING = "NOT_CHARGING"          # vehicle is not currently charging
    PLUGGED_IN = "PLUGGED_IN"              # physically connected, but energy not flowing yet
    AUTHORIZING = "AUTHORIZING"            # waiting for charger/session authorization
    CHARGING = "CHARGING"                  # actively charging
    CHARGE_COMPLETE = "CHARGE_COMPLETE"    # full/target reached, still connected
    STOPPING = "STOPPING"                  # stop requested / winding down
    FAULTED = "FAULTED"                    # charger/vehicle/session fault
    DISCONNECTED = "DISCONNECTED"          # connector removed after a prior charging state


class VehicleAvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    ON_TRIP = "ON_TRIP"
    CHARGING = "CHARGING"
    OFFLINE = "OFFLINE"
    BLOCKED = "BLOCKED"
    MAINTENANCE = "MAINTENANCE"


class VehicleEnergyType(str, enum.Enum):
    EV = "EV"
    HYBRID = "HYBRID"
    ICE = "ICE"


class TransmissionType(str, enum.Enum):
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"


class LockState(str, enum.Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    UNKNOWN = "UNKNOWN"


class DataSource(str, enum.Enum):
    TELEMETRY_PUSH = "TELEMETRY_PUSH"          # device/provider pushed data into our backend
    TELEMETRY_POLL = "TELEMETRY_POLL"          # backend polled provider/OEM and updated row
    CHARGING_WEBHOOK = "CHARGING_WEBHOOK"      # charging system callback updated charging fields
    TRIP_RUNTIME = "TRIP_RUNTIME"              # trip engine/runtime service updated live state
    BOOKING_ENGINE = "BOOKING_ENGINE"          # booking engine changed availability/active assignment
    ADMIN_PANEL = "ADMIN_PANEL"                # explicit admin/operator manual change
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"        # forced operational override outside normal automation
    DERIVED_SYSTEM = "DERIVED_SYSTEM"          # computed/internal aggregation or state derivation
    RECONCILIATION_JOB = "RECONCILIATION_JOB"  # async reconciliation/correction job
    BACKFILL = "BACKFILL"                      # historical backfill/import
    UNKNOWN = "UNKNOWN"


class CleanlinessStatus(str, enum.Enum):
    CLEAN = "CLEAN"
    NEEDS_CLEANING = "NEEDS_CLEANING"
    BLOCKED = "BLOCKED"


class ZoneType(str, enum.Enum):
    RETURN = "RETURN"
    HUB = "HUB"
    PARKING = "PARKING"


class PricingPlanStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    RETIRED = "RETIRED"


class BillingUnit(str, enum.Enum):
    PER_MINUTE = "PER_MINUTE"
    PER_15_MIN = "PER_15_MIN"
    PER_HOUR = "PER_HOUR"
    FLAT = "FLAT"


class RateLineType(str, enum.Enum):
    BASE_TIME = "BASE_TIME"
    PEAK_SURCHARGE = "PEAK_SURCHARGE"
    KM_OVERAGE = "KM_OVERAGE"
    DEPOSIT_HOLD = "DEPOSIT_HOLD"
    CANCELLATION_FEE = "CANCELLATION_FEE"
    LATE_FEE = "LATE_FEE"
    DAMAGE_FEE = "DAMAGE_FEE"
    CLEANING_FEE = "CLEANING_FEE"
    GEOFENCE_FINE = "GEOFENCE_FINE"
    CLAIM_RECOVERY = "CLAIM_RECOVERY"
    TAX = "TAX"
    CHARGING_RAW_COST = "CHARGING_RAW_COST"
    CHARGING_BENEFIT = "CHARGING_BENEFIT"
    PROMO_DISCOUNT = "PROMO_DISCOUNT"
    PROMO_CASHBACK = "PROMO_CASHBACK"
    SUBSCRIPTION_DISCOUNT = "SUBSCRIPTION_DISCOUNT"
    REFUND = "REFUND"
    WALLET_TOPUP = "WALLET_TOPUP"
    WALLET_DEBIT = "WALLET_DEBIT"
    ADJUSTMENT = "ADJUSTMENT"

class KmPolicyType(str, enum.Enum):
    UNLIMITED = "UNLIMITED"
    INCLUDED_PLUS_OVERAGE = "INCLUDED_PLUS_OVERAGE"


class LateFeePolicyType(str, enum.Enum):
    NONE = "NONE"
    FLAT = "FLAT"
    PER_UNIT = "PER_UNIT"
    FLAT_PLUS_PER_UNIT = "FLAT_PLUS_PER_UNIT"


class CancellationFeeType(str, enum.Enum):
    NONE = "NONE"
    FLAT = "FLAT"
    PERCENT = "PERCENT"


class TaxMode(str, enum.Enum):
    EXCLUSIVE = "EXCLUSIVE"
    INCLUSIVE = "INCLUSIVE"


class QuoteStatus(str, enum.Enum):
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class BookingLockStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    CONSUMED = "CONSUMED"


class BookingStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class BookingCancelReason(str, enum.Enum):
    USER_CANCELLED = "USER_CANCELLED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    ADMIN_CANCELLED = "ADMIN_CANCELLED"
    NO_SHOW = "NO_SHOW"
    OTHER = "OTHER"


class TripStatus(str, enum.Enum):
    READY_TO_START = "READY_TO_START"
    ACTIVE = "ACTIVE"
    END_REQUESTED = "END_REQUESTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"
    DISPUTED = "DISPUTED"


class InspectionType(str, enum.Enum):
    PRE_TRIP = "PRE_TRIP"
    POST_TRIP = "POST_TRIP"


class InspectionItemType(str, enum.Enum):
    EXTERIOR = "EXTERIOR"
    INTERIOR = "INTERIOR"
    ODOMETER = "ODOMETER"
    SOC = "SOC"
    TYRES = "TYRES"
    CLEANLINESS = "CLEANLINESS"
    SELFIE = "SELFIE"
    OTHER = "OTHER"


class TripEventType(str, enum.Enum):
    USER_CREATED = "USER_CREATED"
    OTP_VERIFIED = "OTP_VERIFIED"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_APPROVED = "KYC_APPROVED"
    KYC_REJECTED = "KYC_REJECTED"
    KYC_STATUS_CHANGED = "KYC_STATUS_CHANGED"
    QUOTE_CREATED = "QUOTE_CREATED"
    QUOTE_ACCEPTED = "QUOTE_ACCEPTED"
    PAYMENT_AUTHORISED = "PAYMENT_AUTHORISED"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    BOOKING_MODIFIED = "BOOKING_MODIFIED"
    ARRIVED_AT_VEHICLE = "ARRIVED_AT_VEHICLE"
    PRE_TRIP_PHOTOS_UPLOADED = "PRE_TRIP_PHOTOS_UPLOADED"
    TRIP_START_REQUESTED = "TRIP_START_REQUESTED"
    TRIP_STARTED = "TRIP_STARTED"
    TRIP_EXTENSION_REQUESTED = "TRIP_EXTENSION_REQUESTED"
    TRIP_EXTENSION_CONFIRMED = "TRIP_EXTENSION_CONFIRMED"
    TRIP_END_REQUESTED = "TRIP_END_REQUESTED"
    TRIP_ENDED = "TRIP_ENDED"
    POST_TRIP_PHOTOS_UPLOADED = "POST_TRIP_PHOTOS_UPLOADED"
    LATE_RETURN_DETECTED = "LATE_RETURN_DETECTED"
    LATE_FEE_APPLIED = "LATE_FEE_APPLIED"
    DAMAGE_CLAIM_CREATED = "DAMAGE_CLAIM_CREATED"
    DAMAGE_FEE_APPLIED = "DAMAGE_FEE_APPLIED"
    GEOFENCE_WARNING_TRIGGERED = "GEOFENCE_WARNING_TRIGGERED"
    GEOFENCE_VIOLATION_RECORDED = "GEOFENCE_VIOLATION_RECORDED"
    DRIVER_BEHAVIOUR_FLAGGED = "DRIVER_BEHAVIOUR_FLAGGED"
    DRIVER_SCORE_COMPUTED = "DRIVER_SCORE_COMPUTED"
    DAMAGE_REPORTED = "DAMAGE_REPORTED"
    MAINTENANCE_BLOCK_APPLIED = "MAINTENANCE_BLOCK_APPLIED"
    SUPPORT_TICKET_CREATED = "SUPPORT_TICKET_CREATED"
    RISK_FLAG_RAISED = "RISK_FLAG_RAISED"
    ADMIN_ACTION_APPLIED = "ADMIN_ACTION_APPLIED"
    REFUND_INITIATED = "REFUND_INITIATED"
    REFUND_COMPLETED = "REFUND_COMPLETED"

class IncidentType(str, enum.Enum):
    DAMAGE = "DAMAGE"
    CLEANING = "CLEANING"
    BREAKDOWN = "BREAKDOWN"
    LOW_SOC = "LOW_SOC"
    ACCIDENT = "ACCIDENT"
    OTHER = "OTHER"


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    REVIEWING = "REVIEWING"
    RESOLVED = "RESOLVED"
    WAIVED = "WAIVED"


class WalletEntryDirection(str, enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class WalletEntryType(str, enum.Enum):
    TOPUP = "TOPUP"
    BOOKING_HOLD = "BOOKING_HOLD"
    BOOKING_HOLD_RELEASE = "BOOKING_HOLD_RELEASE"
    BOOKING_CHARGE = "BOOKING_CHARGE"
    TRIP_CHARGE = "TRIP_CHARGE"
    LATE_FEE = "LATE_FEE"
    DAMAGE_FEE = "DAMAGE_FEE"
    CLEANING_FEE = "CLEANING_FEE"
    CHARGING_COST = "CHARGING_COST"
    PROMO_CASHBACK = "PROMO_CASHBACK"
    MANUAL_COMPENSATION = "MANUAL_COMPENSATION"
    SUBSCRIPTION_BENEFIT = "SUBSCRIPTION_BENEFIT"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"

class PaymentProvider(str, enum.Enum):
    RAZORPAY = "RAZORPAY"
    CASHFREE = "CASHFREE"
    PAYU = "PAYU"
    MANUAL = "MANUAL"


class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    CARD = "CARD"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"
    BANK_TRANSFER = "BANK_TRANSFER"
    OTHER = "OTHER"


class PaymentPurpose(str, enum.Enum):
    BOOKING_AUTH = "BOOKING_AUTH"
    WALLET_TOPUP = "WALLET_TOPUP"
    TRIP_SETTLEMENT = "TRIP_SETTLEMENT"
    SUBSCRIPTION_PURCHASE = "SUBSCRIPTION_PURCHASE"
    DAMAGE_SETTLEMENT = "DAMAGE_SETTLEMENT"
    CLAIM_SETTLEMENT = "CLAIM_SETTLEMENT"
    REFUND = "REFUND"

class PaymentStatus(str, enum.Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    AUTHORISED = "AUTHORISED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class RefundStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    VOID = "VOID"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"


class ChargingBenefitType(str, enum.Enum):
    FREE = "FREE"
    PERCENT_DISCOUNT = "PERCENT_DISCOUNT"
    FIXED_DISCOUNT = "FIXED_DISCOUNT"
    CASHBACK = "CASHBACK"


class ChargingAuthStatus(str, enum.Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    REQUESTED = "REQUESTED"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    ERROR = "ERROR"


class ChargingSessionStatus(str, enum.Enum):
    INITIATED = "INITIATED"
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"
    SETTLED = "SETTLED"
    FAILED = "FAILED"


class ChargingMatchStatus(str, enum.Enum):
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"
    DISPUTED = "DISPUTED"


class NotificationChannel(str, enum.Enum):
    PUSH = "PUSH"
    SMS = "SMS"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


class NotificationStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AuditActorType(str, enum.Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"
    ADMIN = "ADMIN"
    GATEWAY = "GATEWAY"
    CMS = "CMS"
    TELEMATICS = "TELEMATICS"


class CityStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class GeoFenceType(str, enum.Enum):
    SOFT = "SOFT"
    HARD = "HARD"


class GeoFenceViolationAction(str, enum.Enum):
    WARNING = "WARNING"
    AUTO_FINE = "AUTO_FINE"
    TRIP_END = "TRIP_END"
    BLOCK_NEXT_BOOKING = "BLOCK_NEXT_BOOKING"


class VehicleHealthStatus(str, enum.Enum):
    GOOD = "GOOD"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class TelemetrySource(str, enum.Enum):
    OBD = "OBD"
    OEM_API = "OEM_API"
    IOT_DEVICE = "IOT_DEVICE"
    MANUAL = "MANUAL"


class BatteryHealthStatus(str, enum.Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    REPLACEMENT_REQUIRED = "REPLACEMENT_REQUIRED"


class DrivingBehaviourEvent(str, enum.Enum):
    HARSH_BRAKING = "HARSH_BRAKING"
    RAPID_ACCELERATION = "RAPID_ACCELERATION"
    OVER_SPEEDING = "OVER_SPEEDING"
    IDLE_TOO_LONG = "IDLE_TOO_LONG"


class DriverScoreBand(str, enum.Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    AVERAGE = "AVERAGE"
    POOR = "POOR"


class DamageSeverity(str, enum.Enum):
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    TOTAL_LOSS = "TOTAL_LOSS"


class DamageLiability(str, enum.Enum):
    USER = "USER"
    COMPANY = "COMPANY"
    THIRD_PARTY = "THIRD_PARTY"
    UNDETERMINED = "UNDETERMINED"


class DamageReportStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    WAIVED = "WAIVED"


class ClaimStatus(str, enum.Enum):
    OPEN = "OPEN"
    FILED = "FILED"
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class MaintenanceType(str, enum.Enum):
    ROUTINE = "ROUTINE"
    BREAKDOWN = "BREAKDOWN"
    BATTERY = "BATTERY"
    TYRE = "TYRE"
    SOFTWARE = "SOFTWARE"


class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PromoType(str, enum.Enum):
    FLAT = "FLAT"
    PERCENTAGE = "PERCENTAGE"
    CASHBACK = "CASHBACK"
    FREE_MINUTES = "FREE_MINUTES"


class PromoApplicability(str, enum.Enum):
    FIRST_TRIP = "FIRST_TRIP"
    ALL_USERS = "ALL_USERS"
    SELECTED_USERS = "SELECTED_USERS"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class SubscriptionPlanType(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class SupportTicketCategory(str, enum.Enum):
    PAYMENT = "PAYMENT"
    VEHICLE = "VEHICLE"
    CHARGING = "CHARGING"
    APP = "APP"
    KYC = "KYC"
    OTHER = "OTHER"


class SupportTicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class SupportTicketPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskFlag(str, enum.Enum):
    MULTIPLE_ACCOUNTS = "MULTIPLE_ACCOUNTS"
    PAYMENT_ABUSE = "PAYMENT_ABUSE"
    DAMAGE_FREQUENT = "DAMAGE_FREQUENT"
    LOCATION_MISMATCH = "LOCATION_MISMATCH"


class RiskSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AdminActionType(str, enum.Enum):
    USER_BLOCK = "USER_BLOCK"
    USER_UNBLOCK = "USER_UNBLOCK"
    VEHICLE_BLOCK = "VEHICLE_BLOCK"
    VEHICLE_UNBLOCK = "VEHICLE_UNBLOCK"
    MANUAL_REFUND = "MANUAL_REFUND"


# ============================================================================
# Identity / auth / files
# ============================================================================


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    user_type: Mapped[UserType] = mapped_column(PGEnum(UserType, name="user_type_enum"), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        PGEnum(UserStatus, name="user_status_enum"),
        nullable=False,
        default=UserStatus.PENDING,
        server_default=UserStatus.PENDING.value,
    )
    kyc_status: Mapped[KycStatus] = mapped_column(
        PGEnum(KycStatus, name="kyc_status_enum"),
        nullable=False,
        default=KycStatus.KYC_NOT_STARTED,
        server_default=KycStatus.KYC_NOT_STARTED.value,
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_contact_phone_e164: Mapped[Optional[str]] = mapped_column(String(20))
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    city_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cities.id", ondelete="SET NULL"))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, server_default="IN")
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    suspended_reason: Mapped[Optional[UserSuspendedReason]] = mapped_column(
    PGEnum(UserSuspendedReason, name="user_suspended_reason_enum")
    )
    suspended_reason_note: Mapped[Optional[str]] = mapped_column(Text)

    blacklisted_reason: Mapped[Optional[UserBlacklistedReason]] = mapped_column(
        PGEnum(UserBlacklistedReason, name="user_blacklisted_reason_enum")
    )
    blacklisted_reason_note: Mapped[Optional[str]] = mapped_column(Text)
    risk_hold_bool: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    risk_score_numeric: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    city_ref: Mapped[Optional["City"]] = relationship(back_populates="users")
    devices: Mapped[list["UserDevice"]] = relationship(back_populates="user")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    consents: Mapped[list["UserConsent"]] = relationship(back_populates="user")
    kyc_cases: Mapped[list["KycCase"]] = relationship(back_populates="user")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="user")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    trips: Mapped[list["Trip"]] = relationship(back_populates="user")
    wallet_account: Mapped[Optional["WalletAccount"]] = relationship(back_populates="user", uselist=False)
    subscriptions: Mapped[list["UserSubscription"]] = relationship(back_populates="user")
    promo_redemptions: Mapped[list["PromotionRedemption"]] = relationship(back_populates="user")
    support_tickets: Mapped[list["SupportTicket"]] = relationship(back_populates="user", foreign_keys="SupportTicket.user_id")
    risk_profile: Mapped[Optional["RiskProfile"]] = relationship(back_populates="user", uselist=False)
    safety_profile: Mapped[Optional["UserSafetyProfile"]] = relationship(back_populates="user", uselist=False)

    __table_args__ = (
        Index("ix_users_status", "status"),
        Index("ix_users_kyc_status", "kyc_status"),
        Index("ix_users_city_id", "city_id"),
    )

class UserDevice(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "user_devices"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[DevicePlatform] = mapped_column(PGEnum(DevicePlatform, name="device_platform_enum"), nullable=False)
    device_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(255))
    app_version: Mapped[Optional[str]] = mapped_column(String(50))
    os_version: Mapped[Optional[str]] = mapped_column(String(50))
    push_token: Mapped[Optional[str]] = mapped_column(String(512))
    is_trusted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="devices")

    __table_args__ = (
        UniqueConstraint("user_id", "device_identifier", name="uq_user_devices_user_device_identifier"),
    )


class Session(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("user_devices.id", ondelete="SET NULL"))
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token_jti: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    status: Mapped[SessionStatus] = mapped_column(
        PGEnum(SessionStatus, name="session_status_enum"),
        nullable=False,
        default=SessionStatus.ACTIVE,
        server_default=SessionStatus.ACTIVE.value,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="sessions")

    __table_args__ = (
        Index("ix_sessions_user_status", "user_id", "status"),
        Index("ix_sessions_expires_at", "expires_at"),
    )


class OtpSession(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "otp_sessions"

    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False)
    purpose: Mapped[OtpPurpose] = mapped_column(PGEnum(OtpPurpose, name="otp_purpose_enum"), nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[OtpStatus] = mapped_column(
        PGEnum(OtpStatus, name="otp_status_enum"),
        nullable=False,
        default=OtpStatus.ISSUED,
        server_default=OtpStatus.ISSUED.value,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("ix_otp_sessions_phone_status", "phone_e164", "status"),
        Index("ix_otp_sessions_expires_at", "expires_at"),
    )


class UserConsent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "user_consents"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consent_type: Mapped[ConsentType] = mapped_column(PGEnum(ConsentType, name="consent_type_enum"), nullable=False)
    status: Mapped[ConsentStatus] = mapped_column(PGEnum(ConsentStatus, name="consent_status_enum"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source: Mapped[Optional[ConsentSource]] = mapped_column(
    PGEnum(ConsentSource, name="consent_source_enum")
    )

    user: Mapped["User"] = relationship(back_populates="consents")

    __table_args__ = (
        Index("ix_user_consents_user_type", "user_id", "consent_type"),
    )


class FileObject(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "file_objects"

    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    purpose: Mapped[FilePurpose] = mapped_column(PGEnum(FilePurpose, name="file_purpose_enum"), nullable=False)
    uploaded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        Index("ix_file_objects_purpose", "purpose"),
    )


# ============================================================================
# KYC
# ============================================================================


class KycCase(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "kyc_cases"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[KycStatus] = mapped_column(PGEnum(KycStatus, name="kyc_case_status_enum"), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reject_reason_code: Mapped[Optional[KycRejectReasonCode]] = mapped_column(
        PGEnum(KycRejectReasonCode, name="kyc_reject_reason_code_enum")
    )
    reject_reason_text: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(50))  # manual_upload / digilocker / hybrid
    extracted_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    risk_flags_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    user: Mapped["User"] = relationship(back_populates="kyc_cases", foreign_keys=[user_id])
    documents: Mapped[list["KycDocument"]] = relationship(back_populates="kyc_case", cascade="all, delete-orphan")
    reviews: Mapped[list["KycReview"]] = relationship(back_populates="kyc_case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_kyc_cases_user_status", "user_id", "status"),
        Index("ix_kyc_cases_status_submitted_at", "status", "submitted_at"),
    )


class KycDocument(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "kyc_documents"

    kyc_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kyc_cases.id", ondelete="CASCADE"), nullable=False)
    doc_type: Mapped[KycDocType] = mapped_column(PGEnum(KycDocType, name="kyc_doc_type_enum"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False)
    extracted_fields_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    verified_bool: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    document_number_masked: Mapped[Optional[str]] = mapped_column(String(100))
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)

    kyc_case: Mapped["KycCase"] = relationship(back_populates="documents")

    __table_args__ = (
        UniqueConstraint("kyc_case_id", "doc_type", name="uq_kyc_documents_case_doc_type"),
    )


class KycReview(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "kyc_reviews"

    kyc_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kyc_cases.id", ondelete="CASCADE"), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    from_status: Mapped[Optional[KycStatus]] = mapped_column(PGEnum(KycStatus, name="kyc_review_from_status_enum"))
    to_status: Mapped[KycStatus] = mapped_column(PGEnum(KycStatus, name="kyc_review_to_status_enum"), nullable=False)
    reason_code: Mapped[Optional[KycRejectReasonCode]] = mapped_column(
        PGEnum(KycRejectReasonCode, name="kyc_review_reason_code_enum")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)

    kyc_case: Mapped["KycCase"] = relationship(back_populates="reviews")

    __table_args__ = (
        Index("ix_kyc_reviews_case_created_at", "kyc_case_id", "created_at"),
    )


# ============================================================================
# Fleet / zones / telematics
# ============================================================================


class ReturnZone(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "return_zones"

    city_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cities.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    zone_type: Mapped[ZoneType] = mapped_column(PGEnum(ZoneType, name="zone_type_enum"), nullable=False)
    polygon_geojson: Mapped[dict] = mapped_column(JSONB, nullable=False)
    buffer_radius_m: Mapped[int] = mapped_column(Integer, default=0)
    rules_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    max_vehicle_capacity: Mapped[Optional[int]] = mapped_column(Integer)
    operating_hours_json: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    city: Mapped[Optional["City"]] = relationship(back_populates="return_zones")
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="home_zone")

    __table_args__ = (
        Index("ix_return_zones_zone_type", "zone_type"),
        Index("ix_return_zones_city_id", "city_id"),
    )

class TelematicsDevice(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "telematics_devices"

    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_device_ref: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source: Mapped[TelemetrySource] = mapped_column(
        PGEnum(TelemetrySource, name="telematics_source_enum"),
        nullable=False,
        default=TelemetrySource.IOT_DEVICE,
        server_default=TelemetrySource.IOT_DEVICE.value,
    )
    imei: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50))
    signal_strength: Mapped[Optional[int]] = mapped_column(Integer)

    vehicle: Mapped[Optional["Vehicle"]] = relationship(back_populates="telematics_device", uselist=False)

class Vehicle(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vehicles"

    vehicle_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    vin: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    reg_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    make: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    variant: Mapped[Optional[str]] = mapped_column(String(100))
    model_year: Mapped[Optional[int]] = mapped_column(Integer)
    color: Mapped[Optional[str]] = mapped_column(String(50))
    seating_capacity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="4")
    transmission: Mapped[TransmissionType] = mapped_column(
        PGEnum(TransmissionType, name="transmission_type_enum"),
        nullable=False,
        default=TransmissionType.AUTOMATIC,
        server_default=TransmissionType.AUTOMATIC.value,
    )
    energy_type: Mapped[VehicleEnergyType] = mapped_column(
        PGEnum(VehicleEnergyType, name="vehicle_energy_type_enum"),
        nullable=False,
        default=VehicleEnergyType.EV,
        server_default=VehicleEnergyType.EV.value,
    )
    battery_capacity_kwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    certified_range_km: Mapped[Optional[int]] = mapped_column(Integer)
    battery_health_status: Mapped[Optional[BatteryHealthStatus]] = mapped_column(
        PGEnum(BatteryHealthStatus, name="vehicle_battery_health_status_enum")
    )
    status: Mapped[VehicleStatus] = mapped_column(
        PGEnum(VehicleStatus, name="vehicle_status_enum"),
        nullable=False,
        default=VehicleStatus.ACTIVE,
        server_default=VehicleStatus.ACTIVE.value,
    )
    operating_city_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cities.id", ondelete="SET NULL"))
    home_zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("return_zones.id", ondelete="SET NULL"))
    telematics_device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("telematics_devices.id", ondelete="SET NULL"),
        unique=True,
    )
    cleanliness_status: Mapped[CleanlinessStatus] = mapped_column(
        PGEnum(CleanlinessStatus, name="cleanliness_status_enum"),
        nullable=False,
        default=CleanlinessStatus.CLEAN,
        server_default=CleanlinessStatus.CLEAN.value,
    )
    odometer_km_baseline: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 1))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    operating_city: Mapped[Optional["City"]] = relationship(back_populates="vehicles")
    home_zone: Mapped[Optional["ReturnZone"]] = relationship(back_populates="vehicles")
    telematics_device: Mapped[Optional["TelematicsDevice"]] = relationship(back_populates="vehicle")
    live_status: Mapped[Optional["VehicleLiveStatus"]] = relationship(back_populates="vehicle", uselist=False)
    blackouts: Mapped[list["VehicleBlackoutWindow"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    pricing_plans: Mapped[list["PricingPlan"]] = relationship(back_populates="vehicle")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="vehicle")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="vehicle")
    trips: Mapped[list["Trip"]] = relationship(back_populates="vehicle")
    telemetry_points: Mapped[list["VehicleTelemetryPoint"]] = relationship(back_populates="vehicle")
    health_alerts: Mapped[list["VehicleHealthAlert"]] = relationship(back_populates="vehicle")
    battery_assessments: Mapped[list["BatteryHealthAssessment"]] = relationship(back_populates="vehicle")
    last_charged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    maintenance_jobs: Mapped[list["MaintenanceJob"]] = relationship(back_populates="vehicle")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())


    __table_args__ = (
        Index("ix_vehicles_status", "status"),
        Index("ix_vehicles_home_zone_id", "home_zone_id"),
        Index("ix_vehicles_operating_city_id", "operating_city_id"),
    )

class VehicleLiveStatus(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_live_status"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, unique=True)
    availability_status: Mapped[VehicleAvailabilityStatus] = mapped_column(
        PGEnum(VehicleAvailabilityStatus, name="vehicle_availability_status_enum"),
        nullable=False,
    )
    telemetry_source: Mapped[Optional[TelemetrySource]] = mapped_column(PGEnum(TelemetrySource, name="vehicle_live_telemetry_source_enum"))
    vehicle_health_status: Mapped[Optional[VehicleHealthStatus]] = mapped_column(
        PGEnum(VehicleHealthStatus, name="vehicle_health_status_enum")
    )
    battery_health_status: Mapped[Optional[BatteryHealthStatus]] = mapped_column(
        PGEnum(BatteryHealthStatus, name="live_battery_health_status_enum")
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    soc_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    estimated_range_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    odometer_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 1))
    battery_temp_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    charging_status: Mapped[Optional[ChargingStatus]] = mapped_column(
    PGEnum(ChargingStatus, name="charging_status_enum"
    ))

    lock_state: Mapped[LockState] = mapped_column(
        PGEnum(LockState, name="lock_state_enum"),
        nullable=False,
        default=LockState.UNKNOWN,
        server_default=LockState.UNKNOWN.value,
    )
    active_trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    low_soc_threshold_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    health_flags_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    raw_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    data_source: Mapped[Optional[DataSource]] = mapped_column(
    PGEnum(DataSource, name="vehicle_live_data_source_enum")
    )

    vehicle: Mapped["Vehicle"] = relationship(back_populates="live_status")

    __table_args__ = (
        Index("ix_vehicle_live_status_availability_status", "availability_status"),
        CheckConstraint("(soc_pct IS NULL) OR (soc_pct >= 0 AND soc_pct <= 100)", name="ck_vehicle_live_status_soc_range"),
    )

class VehicleBlackoutWindow(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_blackout_windows"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    maintenance_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("maintenance_jobs.id", ondelete="SET NULL"))
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    vehicle: Mapped["Vehicle"] = relationship(back_populates="blackouts")
    maintenance_job: Mapped[Optional["MaintenanceJob"]] = relationship(back_populates="blackout_windows")

    __table_args__ = (
        CheckConstraint("end_ts > start_ts", name="ck_vehicle_blackout_windows_end_after_start"),
        Index("ix_vehicle_blackout_windows_vehicle_start_end", "vehicle_id", "start_ts", "end_ts"),
    )

class PricingPlan(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pricing_plans"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"))
    status: Mapped[PricingPlanStatus] = mapped_column(
        PGEnum(PricingPlanStatus, name="pricing_plan_status_enum"),
        nullable=False,
        default=PricingPlanStatus.DRAFT,
        server_default=PricingPlanStatus.DRAFT.value,
    )
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    min_booking_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="60")
    max_booking_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    turnaround_buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    billing_unit: Mapped[BillingUnit] = mapped_column(PGEnum(BillingUnit, name="billing_unit_enum"), nullable=False)
    grace_period_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    tax_mode: Mapped[TaxMode] = mapped_column(
        PGEnum(TaxMode, name="tax_mode_enum"),
        nullable=False,
        default=TaxMode.EXCLUSIVE,
        server_default=TaxMode.EXCLUSIVE.value,
    )
    gst_rate_bps: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1800")
    terms_version: Mapped[Optional[str]] = mapped_column(String(50))
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    vehicle: Mapped[Optional["Vehicle"]] = relationship(back_populates="pricing_plans")
    rate_lines: Mapped[list["PricingRateLine"]] = relationship(back_populates="pricing_plan", cascade="all, delete-orphan")
    km_policies: Mapped[list["KmPolicy"]] = relationship(back_populates="pricing_plan", cascade="all, delete-orphan")
    late_fee_policies: Mapped[list["LateFeePolicy"]] = relationship(back_populates="pricing_plan", cascade="all, delete-orphan")
    cancellation_policies: Mapped[list["CancellationPolicy"]] = relationship(back_populates="pricing_plan", cascade="all, delete-orphan")
    deposit_policies: Mapped[list["DepositPolicy"]] = relationship(back_populates="pricing_plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_pricing_plans_vehicle_status", "vehicle_id", "status"),
    )


class PricingRateLine(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pricing_rate_lines"

    pricing_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pricing_plans.id", ondelete="CASCADE"), nullable=False)
    line_type: Mapped[RateLineType] = mapped_column(PGEnum(RateLineType, name="rate_line_type_enum"), nullable=False)
    starts_at_local_time: Mapped[Optional[str]] = mapped_column(String(5))  # HH:MM
    ends_at_local_time: Mapped[Optional[str]] = mapped_column(String(5))    # HH:MM
    weekday_mask: Mapped[Optional[int]] = mapped_column(Integer)            # bitmask Mon..Sun
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    unit_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    pricing_plan: Mapped["PricingPlan"] = relationship(back_populates="rate_lines")

    __table_args__ = (
        Index("ix_pricing_rate_lines_plan_type_active", "pricing_plan_id", "line_type", "is_active"),
    )


class KmPolicy(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "km_policies"

    pricing_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pricing_plans.id", ondelete="CASCADE"), nullable=False)
    policy_type: Mapped[KmPolicyType] = mapped_column(PGEnum(KmPolicyType, name="km_policy_type_enum"), nullable=False)
    included_km_per_booking: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    included_km_per_hour: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    overage_amount_minor_per_km: Mapped[Optional[int]] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())

    pricing_plan: Mapped["PricingPlan"] = relationship(back_populates="km_policies")


class LateFeePolicy(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "late_fee_policies"

    pricing_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pricing_plans.id", ondelete="CASCADE"), nullable=False)
    policy_type: Mapped[LateFeePolicyType] = mapped_column(PGEnum(LateFeePolicyType, name="late_fee_policy_type_enum"), nullable=False)
    grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    flat_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    per_unit_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    unit_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    max_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())

    pricing_plan: Mapped["PricingPlan"] = relationship(back_populates="late_fee_policies")


class CancellationPolicy(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "cancellation_policies"

    pricing_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pricing_plans.id", ondelete="CASCADE"), nullable=False)
    fee_type: Mapped[CancellationFeeType] = mapped_column(
        PGEnum(CancellationFeeType, name="cancellation_fee_type_enum"),
        nullable=False,
    )
    cutoff_minutes_before_start: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    percent_bps: Mapped[Optional[int]] = mapped_column(Integer)
    max_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())

    pricing_plan: Mapped["PricingPlan"] = relationship(back_populates="cancellation_policies")


class DepositPolicy(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "deposit_policies"

    pricing_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pricing_plans.id", ondelete="CASCADE"), nullable=False)
    hold_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    refund_delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    negative_due_block_threshold_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    extension_due_block_threshold_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())

    pricing_plan: Mapped["PricingPlan"] = relationship(back_populates="deposit_policies")


# ============================================================================
# Quotes / bookings / trips
# ============================================================================


class Quote(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "quotes"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    pricing_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pricing_plans.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[QuoteStatus] = mapped_column(
        PGEnum(QuoteStatus, name="quote_status_enum"),
        nullable=False,
        default=QuoteStatus.CREATED,
        server_default=QuoteStatus.CREATED.value,
    )
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    turnaround_buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    total_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    deposit_hold_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    pricing_snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="quotes")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="quotes")
    charge_lines: Mapped[list["QuoteChargeLine"]] = relationship(back_populates="quote", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("end_ts > start_ts", name="ck_quotes_end_after_start"),
        Index("ix_quotes_vehicle_start_end", "vehicle_id", "start_ts", "end_ts"),
        Index("ix_quotes_user_status", "user_id", "status"),
    )


class QuoteChargeLine(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "quote_charge_lines"

    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    line_type: Mapped[RateLineType] = mapped_column(PGEnum(RateLineType, name="quote_line_type_enum"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default="1")
    unit_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    line_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    tax_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    source_entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    source_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    quote: Mapped["Quote"] = relationship(back_populates="charge_lines")

class BookingLock(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "booking_locks"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quote_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("quotes.id", ondelete="SET NULL"))
    status: Mapped[BookingLockStatus] = mapped_column(
        PGEnum(BookingLockStatus, name="booking_lock_status_enum"),
        nullable=False,
        default=BookingLockStatus.ACTIVE,
        server_default=BookingLockStatus.ACTIVE.value,
    )
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("end_ts > start_ts", name="ck_booking_locks_end_after_start"),
        Index("ix_booking_locks_vehicle_status_expires", "vehicle_id", "status", "expires_at"),
    )


class Booking(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    booking_no: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id", ondelete="RESTRICT"), nullable=False)
    pricing_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pricing_plans.id", ondelete="RESTRICT"), nullable=False)
    booking_lock_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("booking_locks.id", ondelete="SET NULL"))
    status: Mapped[BookingStatus] = mapped_column(
        PGEnum(BookingStatus, name="booking_status_enum"),
        nullable=False,
    )
    cancel_reason: Mapped[Optional[BookingCancelReason]] = mapped_column(
        PGEnum(BookingCancelReason, name="booking_cancel_reason_enum")
    )
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    turnaround_buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    terms_version: Mapped[Optional[str]] = mapped_column(String(50))
    pricing_snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    policy_snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    payment_authorised_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    no_show_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="bookings")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="bookings")
    revisions: Mapped[list["BookingRevision"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    payment_intents: Mapped[list["PaymentIntent"]] = relationship(back_populates="booking")
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")
    trip: Mapped[Optional["Trip"]] = relationship(back_populates="booking", uselist=False)

    __table_args__ = (
        CheckConstraint("end_ts > start_ts", name="ck_bookings_end_after_start"),
        Index("ix_bookings_vehicle_status_start_end", "vehicle_id", "status", "start_ts", "end_ts"),
        Index("ix_bookings_user_status", "user_id", "status"),
    )


class BookingRevision(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "booking_revisions"

    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previous_end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    new_start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    new_end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quote_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("quotes.id", ondelete="SET NULL"))
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reason: Mapped[Optional[str]] = mapped_column(Text)

    booking: Mapped["Booking"] = relationship(back_populates="revisions")

    __table_args__ = (
        UniqueConstraint("booking_id", "revision_no", name="uq_booking_revisions_booking_revision_no"),
    )


class Trip(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "trips"

    trip_no: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[TripStatus] = mapped_column(PGEnum(TripStatus, name="trip_status_enum"), nullable=False)
    booked_start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    booked_end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_end_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    start_odometer_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 1))
    end_odometer_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 1))
    start_soc_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    end_soc_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pickup_zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("return_zones.id", ondelete="SET NULL"))
    return_zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("return_zones.id", ondelete="SET NULL"))
    return_zone_ok_bool: Mapped[Optional[bool]] = mapped_column(Boolean)
    extension_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    overtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    pricing_snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    checklist_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    booking: Mapped["Booking"] = relationship(back_populates="trip")
    user: Mapped["User"] = relationship(back_populates="trips")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="trips")
    inspections: Mapped[list["TripInspection"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    events: Mapped[list["TripEvent"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    extensions: Mapped[list["TripExtension"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    incidents: Mapped[list["TripIncident"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    billing_ledger_entries: Mapped[list["BillingLedgerEntry"]] = relationship(back_populates="trip")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="trip")
    charging_sessions: Mapped[list["ChargingSession"]] = relationship(back_populates="trip")
    geofence_violations: Mapped[list["GeofenceViolation"]] = relationship(back_populates="trip")
    driving_events: Mapped[list["TripDrivingEvent"]] = relationship(back_populates="trip")
    driver_score: Mapped[Optional["TripDriverScore"]] = relationship(back_populates="trip", uselist=False)
    damage_reports: Mapped[list["DamageReport"]] = relationship(back_populates="trip")

    __table_args__ = (
        Index("ix_trips_user_status", "user_id", "status"),
        Index("ix_trips_vehicle_status", "vehicle_id", "status"),
        Index("ix_trips_booked_start_end", "booked_start_ts", "booked_end_ts"),
    )

class TripInspection(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "trip_inspections"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    inspection_type: Mapped[InspectionType] = mapped_column(PGEnum(InspectionType, name="inspection_type_enum"), nullable=False)
    captured_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    trip: Mapped["Trip"] = relationship(back_populates="inspections")
    items: Mapped[list["TripInspectionItem"]] = relationship(back_populates="inspection", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_trip_inspections_trip_type", "trip_id", "inspection_type"),
    )


class TripInspectionItem(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "trip_inspection_items"

    inspection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trip_inspections.id", ondelete="CASCADE"), nullable=False)
    item_type: Mapped[InspectionItemType] = mapped_column(PGEnum(InspectionItemType, name="inspection_item_type_enum"), nullable=False)
    text_value: Mapped[Optional[str]] = mapped_column(Text)
    numeric_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3))
    bool_value: Mapped[Optional[bool]] = mapped_column(Boolean)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    inspection: Mapped["TripInspection"] = relationship(back_populates="items")
    media: Mapped[list["TripInspectionMedia"]] = relationship(back_populates="inspection_item", cascade="all, delete-orphan")


class TripInspectionMedia(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "trip_inspection_media"

    inspection_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trip_inspection_items.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(255))

    inspection_item: Mapped["TripInspectionItem"] = relationship(back_populates="media")


class TripExtension(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "trip_extensions"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    request_no: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_end_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    quote_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("quotes.id", ondelete="SET NULL"))
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    was_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    reason: Mapped[Optional[str]] = mapped_column(Text)

    trip: Mapped["Trip"] = relationship(back_populates="extensions")

    __table_args__ = (
        UniqueConstraint("trip_id", "request_no", name="uq_trip_extensions_trip_request_no"),
    )


class TripEvent(UUIDPKMixin, Base):
    __tablename__ = "trip_events"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    event_type: Mapped[TripEventType] = mapped_column(PGEnum(TripEventType, name="trip_event_type_enum"), nullable=False)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    actor_type: Mapped[AuditActorType] = mapped_column(PGEnum(AuditActorType, name="trip_event_actor_type_enum"), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    trip: Mapped["Trip"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_trip_events_trip_ts", "trip_id", "ts"),
        Index("ix_trip_events_trip_event_type", "trip_id", "event_type"),
    )


class TripIncident(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "trip_incidents"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    incident_type: Mapped[IncidentType] = mapped_column(PGEnum(IncidentType, name="incident_type_enum"), nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        PGEnum(IncidentStatus, name="incident_status_enum"),
        nullable=False,
        default=IncidentStatus.OPEN,
        server_default=IncidentStatus.OPEN.value,
    )
    reported_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    estimated_fee_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    final_fee_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    trip: Mapped["Trip"] = relationship(back_populates="incidents")


# ============================================================================
# Wallet / payments / billing / invoices
# ============================================================================


class WalletAccount(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "wallet_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    available_balance_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    reserved_balance_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    due_balance_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    last_recomputed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="wallet_account")
    entries: Mapped[list["WalletLedgerEntry"]] = relationship(back_populates="wallet_account", cascade="all, delete-orphan")


class WalletLedgerEntry(UUIDPKMixin, Base):
    __tablename__ = "wallet_ledger_entries"

    wallet_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallet_accounts.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    direction: Mapped[WalletEntryDirection] = mapped_column(
        PGEnum(WalletEntryDirection, name="wallet_entry_direction_enum"),
        nullable=False,
    )
    entry_type: Mapped[WalletEntryType] = mapped_column(PGEnum(WalletEntryType, name="wallet_entry_type_enum"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    reserved_after_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    due_after_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"))
    source_entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    source_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    reference: Mapped[Optional[str]] = mapped_column(String(255))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    wallet_account: Mapped["WalletAccount"] = relationship(back_populates="entries")

    __table_args__ = (
        Index("ix_wallet_ledger_entries_wallet_ts", "wallet_account_id", "ts"),
        Index("ix_wallet_ledger_entries_source_entity", "source_entity_type", "source_entity_id"),
    )

class PaymentIntent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "payment_intents"

    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    provider: Mapped[PaymentProvider] = mapped_column(PGEnum(PaymentProvider, name="payment_provider_enum"), nullable=False)
    purpose: Mapped[PaymentPurpose] = mapped_column(PGEnum(PaymentPurpose, name="payment_purpose_enum"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    provider_order_ref: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[PaymentStatus] = mapped_column(PGEnum(PaymentStatus, name="payment_intent_status_enum"), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    booking: Mapped[Optional["Booking"]] = relationship(back_populates="payment_intents")

    __table_args__ = (
        Index("ix_payment_intents_booking_status", "booking_id", "status"),
        Index("ix_payment_intents_user_status", "user_id", "status"),
    )


class Payment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    payment_intent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("payment_intents.id", ondelete="SET NULL"))
    provider: Mapped[PaymentProvider] = mapped_column(PGEnum(PaymentProvider, name="payment_provider_payment_enum"), nullable=False)
    purpose: Mapped[PaymentPurpose] = mapped_column(PGEnum(PaymentPurpose, name="payment_purpose_payment_enum"), nullable=False)
    method: Mapped[Optional[PaymentMethod]] = mapped_column(PGEnum(PaymentMethod, name="payment_method_enum"))
    status: Mapped[PaymentStatus] = mapped_column(PGEnum(PaymentStatus, name="payment_status_enum"), nullable=False)
    provider_payment_ref: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    provider_order_ref: Mapped[Optional[str]] = mapped_column(String(255))
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    gateway_fee_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    tax_on_gateway_fee_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    authorised_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[Optional[str]] = mapped_column(String(100))
    failure_message: Mapped[Optional[str]] = mapped_column(Text)
    raw_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    booking: Mapped[Optional["Booking"]] = relationship(back_populates="payments")

    __table_args__ = (
        Index("ix_payments_booking_status", "booking_id", "status"),
        Index("ix_payments_trip_status", "trip_id", "status"),
        Index("ix_payments_user_created_at", "user_id", "created_at"),
    )


class PaymentWebhookEvent(UUIDPKMixin, Base):
    __tablename__ = "payment_webhook_events"

    provider: Mapped[PaymentProvider] = mapped_column(PGEnum(PaymentProvider, name="payment_provider_webhook_enum"), nullable=False)
    provider_event_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "provider_event_ref", name="uq_payment_webhook_events_provider_event_ref"),
        Index("ix_payment_webhook_events_payment_id", "payment_id"),
    )


class Refund(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "refunds"

    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False)
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    status: Mapped[RefundStatus] = mapped_column(PGEnum(RefundStatus, name="refund_status_enum"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    provider_ref: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    raw_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class BillingLedgerEntry(UUIDPKMixin, Base):
    __tablename__ = "billing_ledger_entries"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    line_type: Mapped[RateLineType] = mapped_column(PGEnum(RateLineType, name="billing_line_type_enum"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default="1")
    unit_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    tax_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    reference_code: Mapped[Optional[str]] = mapped_column(String(100))
    source_entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    source_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    trip: Mapped["Trip"] = relationship(back_populates="billing_ledger_entries")

    __table_args__ = (
        Index("ix_billing_ledger_entries_trip_ts", "trip_id", "ts"),
        Index("ix_billing_ledger_entries_trip_line_type", "trip_id", "line_type"),
        Index("ix_billing_ledger_entries_source_entity", "source_entity_type", "source_entity_id"),
    )

class Invoice(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "invoices"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="RESTRICT"), nullable=False)
    invoice_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        PGEnum(InvoiceStatus, name="invoice_status_enum"),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        server_default=InvoiceStatus.DRAFT.value,
    )
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    subtotal_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    tax_total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    total_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    pdf_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("file_objects.id", ondelete="SET NULL"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    trip: Mapped["Trip"] = relationship(back_populates="invoices")
    lines: Mapped[list["InvoiceLine"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_invoices_trip_status", "trip_id", "status"),
    )


class InvoiceLine(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    line_type: Mapped[RateLineType] = mapped_column(PGEnum(RateLineType, name="invoice_line_type_enum"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default="1")
    unit_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    tax_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    source_entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    source_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    invoice: Mapped["Invoice"] = relationship(back_populates="lines")

class ChargingStation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "charging_stations"

    city_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cities.id", ondelete="SET NULL"))
    station_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_company_owned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    address_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    cms_station_ref: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())

    city: Mapped[Optional["City"]] = relationship(back_populates="charging_stations")
    connectors: Mapped[list["ChargingConnector"]] = relationship(back_populates="station", cascade="all, delete-orphan")
    benefit_policies: Mapped[list["ChargingBenefitPolicy"]] = relationship(back_populates="station", cascade="all, delete-orphan")
    sessions: Mapped[list["ChargingSession"]] = relationship(back_populates="station")

    __table_args__ = (
        Index("ix_charging_stations_company_owned_active", "is_company_owned", "is_active"),
        Index("ix_charging_stations_city_id", "city_id"),
    )

class ChargingConnector(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "charging_connectors"

    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("charging_stations.id", ondelete="CASCADE"), nullable=False)
    connector_code: Mapped[str] = mapped_column(String(100), nullable=False)
    connector_type: Mapped[Optional[str]] = mapped_column(String(100))
    tariff_code: Mapped[Optional[str]] = mapped_column(String(100))
    cms_connector_ref: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    max_power_kw: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())

    station: Mapped["ChargingStation"] = relationship(back_populates="connectors")

    __table_args__ = (
        UniqueConstraint("station_id", "connector_code", name="uq_charging_connectors_station_connector_code"),
    )


class ChargingBenefitPolicy(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "charging_benefit_policies"

    station_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("charging_stations.id", ondelete="CASCADE"))
    benefit_type: Mapped[ChargingBenefitType] = mapped_column(
        PGEnum(ChargingBenefitType, name="charging_benefit_type_enum"),
        nullable=False,
    )
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cap_kwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    cap_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    min_session_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    percent_bps: Mapped[Optional[int]] = mapped_column(Integer)
    fixed_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    cashback_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    eligible_tariff_codes: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    rule_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())

    station: Mapped[Optional["ChargingStation"]] = relationship(back_populates="benefit_policies")

    __table_args__ = (
        Index("ix_charging_benefit_policies_station_active_from", "station_id", "active_from"),
    )


class ChargingSession(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "charging_sessions"

    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("charging_stations.id", ondelete="RESTRICT"), nullable=False)
    connector_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("charging_connectors.id", ondelete="SET NULL"))
    cms_session_ref: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    status: Mapped[ChargingSessionStatus] = mapped_column(
        PGEnum(ChargingSessionStatus, name="charging_session_status_enum"),
        nullable=False,
        default=ChargingSessionStatus.INITIATED,
        server_default=ChargingSessionStatus.INITIATED.value,
    )
    auth_status: Mapped[ChargingAuthStatus] = mapped_column(
        PGEnum(ChargingAuthStatus, name="charging_auth_status_enum"),
        nullable=False,
        default=ChargingAuthStatus.NOT_REQUESTED,
        server_default=ChargingAuthStatus.NOT_REQUESTED.value,
    )
    match_status: Mapped[ChargingMatchStatus] = mapped_column(
        PGEnum(ChargingMatchStatus, name="charging_match_status_enum"),
        nullable=False,
        default=ChargingMatchStatus.UNMATCHED,
        server_default=ChargingMatchStatus.UNMATCHED.value,
    )
    start_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    kwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    raw_cost_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    benefit_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    final_cost_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    benefit_policy_snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    matching_notes: Mapped[Optional[str]] = mapped_column(Text)
    raw_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    trip: Mapped[Optional["Trip"]] = relationship(back_populates="charging_sessions")
    station: Mapped["ChargingStation"] = relationship(back_populates="sessions")
    events: Mapped[list["ChargingSessionEvent"]] = relationship(back_populates="charging_session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_charging_sessions_trip_match_status", "trip_id", "match_status"),
        Index("ix_charging_sessions_station_start_ts", "station_id", "start_ts"),
    )


class ChargingSessionEvent(UUIDPKMixin, Base):
    __tablename__ = "charging_session_events"

    charging_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("charging_sessions.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[AuditActorType] = mapped_column(PGEnum(AuditActorType, name="charging_event_actor_type_enum"), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    charging_session: Mapped["ChargingSession"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_charging_session_events_session_ts", "charging_session_id", "ts"),
    )


# ============================================================================
# Cities / geofences / telemetry / damage / maintenance / growth / support
# ============================================================================


class City(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "cities"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[Optional[str]] = mapped_column(String(10))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, server_default="IN")
    status: Mapped[CityStatus] = mapped_column(
        PGEnum(CityStatus, name="city_status_enum"),
        nullable=False,
        default=CityStatus.ACTIVE,
        server_default=CityStatus.ACTIVE.value,
    )
    center_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    center_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    service_area_geojson: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    users: Mapped[list["User"]] = relationship(back_populates="city_ref")
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="operating_city")
    return_zones: Mapped[list["ReturnZone"]] = relationship(back_populates="city")
    charging_stations: Mapped[list["ChargingStation"]] = relationship(back_populates="city")
    geofences: Mapped[list["Geofence"]] = relationship(back_populates="city")

    __table_args__ = (
        UniqueConstraint("name", "state_code", "country_code", name="uq_cities_name_state_country"),
        Index("ix_cities_status", "status"),
    )


class Geofence(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "geofences"

    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    geofence_type: Mapped[GeoFenceType] = mapped_column(PGEnum(GeoFenceType, name="geofence_type_enum"), nullable=False)
    violation_action: Mapped[GeoFenceViolationAction] = mapped_column(
        PGEnum(GeoFenceViolationAction, name="geofence_violation_action_enum"),
        nullable=False,
    )
    polygon_geojson: Mapped[dict] = mapped_column(JSONB, nullable=False)
    penalty_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    rules_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    city: Mapped["City"] = relationship(back_populates="geofences")
    assignments: Mapped[list["GeofenceAssignment"]] = relationship(back_populates="geofence", cascade="all, delete-orphan")
    violations: Mapped[list["GeofenceViolation"]] = relationship(back_populates="geofence", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_geofences_city_active", "city_id", "is_active"),
    )


class GeofenceAssignment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "geofence_assignments"

    geofence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("geofences.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"))
    city_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"))
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    geofence: Mapped["Geofence"] = relationship(back_populates="assignments")
    vehicle: Mapped[Optional["Vehicle"]] = relationship()
    city: Mapped[Optional["City"]] = relationship()

    __table_args__ = (
        CheckConstraint("vehicle_id IS NOT NULL OR city_id IS NOT NULL", name="ck_geofence_assignments_target_present"),
        CheckConstraint("effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from", name="ck_geofence_assignments_end_after_start"),
    )


class GeofenceViolation(UUIDPKMixin, Base):
    __tablename__ = "geofence_violations"

    geofence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("geofences.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    action_taken: Mapped[GeoFenceViolationAction] = mapped_column(
        PGEnum(GeoFenceViolationAction, name="geofence_violation_taken_action_enum"),
        nullable=False,
    )
    penalty_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    warning_sent_bool: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    billing_ledger_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("billing_ledger_entries.id", ondelete="SET NULL"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    geofence: Mapped["Geofence"] = relationship(back_populates="violations")
    vehicle: Mapped["Vehicle"] = relationship()
    trip: Mapped[Optional["Trip"]] = relationship(back_populates="geofence_violations")
    user: Mapped[Optional["User"]] = relationship()

    __table_args__ = (
        Index("ix_geofence_violations_trip_detected_at", "trip_id", "detected_at"),
        Index("ix_geofence_violations_vehicle_detected_at", "vehicle_id", "detected_at"),
    )


class VehicleTelemetryPoint(UUIDPKMixin, Base):
    __tablename__ = "vehicle_telemetry_points"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    telematics_device_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("telematics_devices.id", ondelete="SET NULL"))
    source: Mapped[TelemetrySource] = mapped_column(PGEnum(TelemetrySource, name="telemetry_point_source_enum"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    soc_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    estimated_range_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    odometer_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 1))
    speed_kmph: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    battery_temp_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    charging_bool: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    raw_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    vehicle: Mapped["Vehicle"] = relationship(back_populates="telemetry_points")
    telematics_device: Mapped[Optional["TelematicsDevice"]] = relationship()

    __table_args__ = (
        Index("ix_vehicle_telemetry_points_vehicle_recorded_at", "vehicle_id", "recorded_at"),
    )


class VehicleHealthAlert(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_health_alerts"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    telemetry_point_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("vehicle_telemetry_points.id", ondelete="SET NULL"))
    status: Mapped[VehicleHealthStatus] = mapped_column(PGEnum(VehicleHealthStatus, name="vehicle_health_alert_status_enum"), nullable=False)
    alert_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    raised_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    vehicle: Mapped["Vehicle"] = relationship(back_populates="health_alerts")
    telemetry_point: Mapped[Optional["VehicleTelemetryPoint"]] = relationship()

    __table_args__ = (
        Index("ix_vehicle_health_alerts_vehicle_raised_at", "vehicle_id", "raised_at"),
    )


class BatteryHealthAssessment(UUIDPKMixin, Base):
    __tablename__ = "battery_health_assessments"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    battery_health_status: Mapped[BatteryHealthStatus] = mapped_column(
        PGEnum(BatteryHealthStatus, name="battery_health_assessment_status_enum"),
        nullable=False,
    )
    soh_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    assessment_source: Mapped[TelemetrySource] = mapped_column(PGEnum(TelemetrySource, name="battery_health_assessment_source_enum"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    vehicle: Mapped["Vehicle"] = relationship(back_populates="battery_assessments")

    __table_args__ = (
        Index("ix_battery_health_assessments_vehicle_assessed_at", "vehicle_id", "assessed_at"),
    )


class TripDrivingEvent(UUIDPKMixin, Base):
    __tablename__ = "trip_driving_events"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    event_type: Mapped[DrivingBehaviourEvent] = mapped_column(PGEnum(DrivingBehaviourEvent, name="driving_behaviour_event_enum"), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    speed_kmph: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    severity_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    source: Mapped[TelemetrySource] = mapped_column(PGEnum(TelemetrySource, name="trip_driving_event_source_enum"), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    trip: Mapped["Trip"] = relationship(back_populates="driving_events")
    vehicle: Mapped["Vehicle"] = relationship()
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("ix_trip_driving_events_trip_detected_at", "trip_id", "detected_at"),
    )


class TripDriverScore(UUIDPKMixin, Base):
    __tablename__ = "trip_driver_scores"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    score_numeric: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    score_band: Mapped[DriverScoreBand] = mapped_column(PGEnum(DriverScoreBand, name="driver_score_band_enum"), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    breakdown_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    trip: Mapped["Trip"] = relationship(back_populates="driver_score")
    user: Mapped["User"] = relationship()
    vehicle: Mapped["Vehicle"] = relationship()


class UserSafetyProfile(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "user_safety_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    lifetime_score_numeric: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    current_score_band: Mapped[Optional[DriverScoreBand]] = mapped_column(PGEnum(DriverScoreBand, name="user_safety_profile_band_enum"))
    last_computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    breakdown_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    user: Mapped["User"] = relationship(back_populates="safety_profile")


class DamageReport(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "damage_reports"

    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    trip_incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trip_incidents.id", ondelete="SET NULL"))
    reported_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    severity: Mapped[DamageSeverity] = mapped_column(PGEnum(DamageSeverity, name="damage_severity_enum"), nullable=False)
    liability: Mapped[DamageLiability] = mapped_column(PGEnum(DamageLiability, name="damage_liability_enum"), nullable=False)
    status: Mapped[DamageReportStatus] = mapped_column(
        PGEnum(DamageReportStatus, name="damage_report_status_enum"),
        nullable=False,
        default=DamageReportStatus.OPEN,
        server_default=DamageReportStatus.OPEN.value,
    )
    panel_name: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    estimated_cost_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    final_cost_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    trip: Mapped["Trip"] = relationship(back_populates="damage_reports")
    vehicle: Mapped["Vehicle"] = relationship()
    trip_incident: Mapped[Optional["TripIncident"]] = relationship()
    media: Mapped[list["DamageMedia"]] = relationship(back_populates="damage_report", cascade="all, delete-orphan")
    claims: Mapped[list["ClaimCase"]] = relationship(back_populates="damage_report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_damage_reports_trip_status", "trip_id", "status"),
        Index("ix_damage_reports_vehicle_reported_at", "vehicle_id", "reported_at"),
    )


class DamageMedia(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "damage_media"

    damage_report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("damage_reports.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    damage_report: Mapped["DamageReport"] = relationship(back_populates="media")
    file: Mapped["FileObject"] = relationship()


class ClaimCase(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "claim_cases"

    damage_report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("damage_reports.id", ondelete="CASCADE"), nullable=False)
    claim_no: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    insurer_name: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[ClaimStatus] = mapped_column(
        PGEnum(ClaimStatus, name="claim_status_enum"),
        nullable=False,
        default=ClaimStatus.OPEN,
        server_default=ClaimStatus.OPEN.value,
    )
    claim_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    settled_amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    damage_report: Mapped["DamageReport"] = relationship(back_populates="claims")


class MaintenanceJob(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_jobs"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(PGEnum(MaintenanceType, name="maintenance_type_enum"), nullable=False)
    status: Mapped[MaintenanceStatus] = mapped_column(PGEnum(MaintenanceStatus, name="maintenance_status_enum"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    scheduled_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    scheduled_end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    vendor_name: Mapped[Optional[str]] = mapped_column(String(255))
    cost_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    vehicle: Mapped["Vehicle"] = relationship(back_populates="maintenance_jobs")
    blackout_windows: Mapped[list["VehicleBlackoutWindow"]] = relationship(back_populates="maintenance_job")
    attachments: Mapped[list["MaintenanceAttachment"]] = relationship(back_populates="maintenance_job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_maintenance_jobs_vehicle_status", "vehicle_id", "status"),
    )


class MaintenanceAttachment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_attachments"

    maintenance_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("maintenance_jobs.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(255))

    maintenance_job: Mapped["MaintenanceJob"] = relationship(back_populates="attachments")
    file: Mapped["FileObject"] = relationship()


class Promotion(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "promotions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    promo_code: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    promo_type: Mapped[PromoType] = mapped_column(PGEnum(PromoType, name="promo_type_enum"), nullable=False)
    applicability: Mapped[PromoApplicability] = mapped_column(PGEnum(PromoApplicability, name="promo_applicability_enum"), nullable=False)
    amount_minor: Mapped[Optional[int]] = mapped_column(BigInteger)
    percent_value_bps: Mapped[Optional[int]] = mapped_column(Integer)
    free_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    max_redemptions_total: Mapped[Optional[int]] = mapped_column(Integer)
    max_redemptions_per_user: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    rules_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    redemptions: Mapped[list["PromotionRedemption"]] = relationship(back_populates="promotion")

    __table_args__ = (
        Index("ix_promotions_code_active", "promo_code", "is_active"),
    )


class PromotionRedemption(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "promotion_redemptions"

    promotion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quote_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("quotes.id", ondelete="SET NULL"))
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    benefit_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    promotion: Mapped["Promotion"] = relationship(back_populates="redemptions")
    user: Mapped["User"] = relationship(back_populates="promo_redemptions")

    __table_args__ = (
        Index("ix_promotion_redemptions_user_redeemed_at", "user_id", "redeemed_at"),
    )


class SubscriptionPlan(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "subscription_plans"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_type: Mapped[SubscriptionPlanType] = mapped_column(PGEnum(SubscriptionPlanType, name="subscription_plan_type_enum"), nullable=False)
    price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    billing_cycle_days: Mapped[int] = mapped_column(Integer, nullable=False)
    benefits_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())

    subscriptions: Mapped[list["UserSubscription"]] = relationship(back_populates="subscription_plan")


class UserSubscription(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "user_subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(PGEnum(SubscriptionStatus, name="subscription_status_enum"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    subscription_plan: Mapped["SubscriptionPlan"] = relationship(back_populates="subscriptions")
    usage_entries: Mapped[list["SubscriptionUsageLedger"]] = relationship(back_populates="user_subscription")

    __table_args__ = (
        Index("ix_user_subscriptions_user_status", "user_id", "status"),
    )


class SubscriptionUsageLedger(UUIDPKMixin, Base):
    __tablename__ = "subscription_usage_ledger"

    user_subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_subscriptions.id", ondelete="CASCADE"), nullable=False)
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    quote_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("quotes.id", ondelete="SET NULL"))
    usage_type: Mapped[str] = mapped_column(String(100), nullable=False)
    units_used: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default="0")
    benefit_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    user_subscription: Mapped["UserSubscription"] = relationship(back_populates="usage_entries")

    __table_args__ = (
        Index("ix_subscription_usage_ledger_subscription_used_at", "user_subscription_id", "used_at"),
    )


class SupportTicket(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "support_tickets"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[SupportTicketCategory] = mapped_column(PGEnum(SupportTicketCategory, name="support_ticket_category_enum"), nullable=False)
    status: Mapped[SupportTicketStatus] = mapped_column(PGEnum(SupportTicketStatus, name="support_ticket_status_enum"), nullable=False)
    priority: Mapped[SupportTicketPriority] = mapped_column(
        PGEnum(SupportTicketPriority, name="support_ticket_priority_enum"),
        nullable=False,
        default=SupportTicketPriority.MEDIUM,
        server_default=SupportTicketPriority.MEDIUM.value,
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    user: Mapped["User"] = relationship(back_populates="support_tickets", foreign_keys=[user_id])
    messages: Mapped[list["SupportTicketMessage"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    attachments: Mapped[list["SupportTicketAttachment"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    links: Mapped[list["SupportTicketLink"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_support_tickets_user_status", "user_id", "status"),
        Index("ix_support_tickets_assigned_status", "assigned_to_user_id", "status"),
    )


class SupportTicketMessage(UUIDPKMixin, Base):
    __tablename__ = "support_ticket_messages"

    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    author_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    is_internal_note: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    ticket: Mapped["SupportTicket"] = relationship(back_populates="messages")


class SupportTicketAttachment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "support_ticket_attachments"

    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False)
    uploaded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    ticket: Mapped["SupportTicket"] = relationship(back_populates="attachments")
    file: Mapped["FileObject"] = relationship()


class SupportTicketLink(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "support_ticket_links"

    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    ticket: Mapped["SupportTicket"] = relationship(back_populates="links")

    __table_args__ = (
        Index("ix_support_ticket_links_entity", "entity_type", "entity_id"),
    )


class RiskFlagRecord(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "risk_flag_records"

    flag_type: Mapped[RiskFlag] = mapped_column(PGEnum(RiskFlag, name="risk_flag_enum"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    raised_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    severity: Mapped[RiskSeverity] = mapped_column(PGEnum(RiskSeverity, name="risk_severity_enum"), nullable=False)
    source_system: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        Index("ix_risk_flag_records_user_raised_at", "user_id", "raised_at"),
        Index("ix_risk_flag_records_entity", "entity_type", "entity_id"),
    )


class RiskProfile(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "risk_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    score_numeric: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    is_booking_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    is_payment_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    last_computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    breakdown_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    user: Mapped["User"] = relationship(back_populates="risk_profile")


class AdminAction(UUIDPKMixin, Base):
    __tablename__ = "admin_actions"

    action_type: Mapped[AdminActionType] = mapped_column(PGEnum(AdminActionType, name="admin_action_type_enum"), nullable=False)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    target_entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        Index("ix_admin_actions_target", "target_entity_type", "target_entity_id"),
        Index("ix_admin_actions_actor_created_at", "actor_user_id", "created_at"),
    )


# ============================================================================
# Notifications / audit / outbox
# ============================================================================


class Notification(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(PGEnum(NotificationChannel, name="notification_channel_enum"), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        PGEnum(NotificationStatus, name="notification_status_enum"),
        nullable=False,
        default=NotificationStatus.QUEUED,
        server_default=NotificationStatus.QUEUED.value,
    )
    template_key: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text)
    related_booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    related_trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("trips.id", ondelete="SET NULL"))
    send_after_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    provider_message_ref: Mapped[Optional[str]] = mapped_column(String(255))
    failure_message: Mapped[Optional[str]] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_send_after_status", "send_after_ts", "status"),
    )


class AuditEvent(UUIDPKMixin, Base):
    __tablename__ = "audit_events"

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actor_type: Mapped[AuditActorType] = mapped_column(PGEnum(AuditActorType, name="audit_actor_type_enum"), nullable=False)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        Index("ix_audit_events_entity", "entity_type", "entity_id"),
        Index("ix_audit_events_ts", "ts"),
    )


class OutboxEvent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "outbox_events"

    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("ix_outbox_events_unpublished", "published_at"),
        Index("ix_outbox_events_aggregate", "aggregate_type", "aggregate_id"),
    )


# ============================================================================
# Migration notes
# ============================================================================

# IMPORTANT POSTGRES MIGRATION REQUIREMENTS
# 1. Enable extension: btree_gist
# 2. Add exclusion constraints in Alembic, not only here in ORM metadata:
#
#    bookings:
#      EXCLUDE USING gist (
#          vehicle_id WITH =,
#          tstzrange(start_ts, end_ts, '[)') WITH &&
#      )
#      WHERE (status IN ('PENDING_PAYMENT', 'CONFIRMED', 'IN_PROGRESS'))
#
#    booking_locks:
#      EXCLUDE USING gist (
#          vehicle_id WITH =,
#          tstzrange(start_ts, end_ts, '[)') WITH &&
#      )
#      WHERE (status = 'ACTIVE')
#
#    vehicle_blackout_windows:
#      EXCLUDE USING gist (
#          vehicle_id WITH =,
#          tstzrange(start_ts, end_ts, '[)') WITH &&
#      )
#
# 3. If geo queries become important, use PostGIS and convert polygon_geojson into geometry.

# 4. New geofence/service-area polygons also benefit from PostGIS if spatial enforcement becomes strict.

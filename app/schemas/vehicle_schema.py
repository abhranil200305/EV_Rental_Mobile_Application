#app/schemas/vehicle_schema.py
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.db.schema import (
    TransmissionType,
    VehicleEnergyType,
    BatteryHealthStatus,
    CleanlinessStatus,
    VehicleStatus
)


# -----------------------------
# CREATE VEHICLE
# -----------------------------
class VehicleCreateRequest(BaseModel):
    vehicle_code: str
    reg_no: str
    model: str

    vin: Optional[str] = None
    make: Optional[str] = None
    variant: Optional[str] = None
    model_year: Optional[int] = None
    color: Optional[str] = None

    seating_capacity: int = 4
    transmission: TransmissionType = TransmissionType.AUTOMATIC
    energy_type: VehicleEnergyType = VehicleEnergyType.EV

    battery_capacity_kwh: Optional[Decimal] = None
    certified_range_km: Optional[int] = None
    battery_health_status: Optional[BatteryHealthStatus] = None

    operating_city_id: Optional[UUID] = None
    home_zone_id: Optional[UUID] = None
    telematics_device_id: Optional[UUID] = None

    cleanliness_status: CleanlinessStatus = CleanlinessStatus.CLEAN
    odometer_km_baseline: Optional[Decimal] = None
    notes: Optional[str] = None


# -----------------------------
# UPDATE VEHICLE
# -----------------------------
class VehicleUpdateRequest(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    model_year: Optional[int] = None
    color: Optional[str] = None

    seating_capacity: Optional[int] = None
    transmission: Optional[TransmissionType] = None
    energy_type: Optional[VehicleEnergyType] = None

    battery_capacity_kwh: Optional[Decimal] = None
    certified_range_km: Optional[int] = None
    battery_health_status: Optional[BatteryHealthStatus] = None

    operating_city_id: Optional[UUID] = None
    home_zone_id: Optional[UUID] = None
    telematics_device_id: Optional[UUID] = None

    cleanliness_status: Optional[CleanlinessStatus] = None
    odometer_km_baseline: Optional[Decimal] = None
    notes: Optional[str] = None


# -----------------------------
# BLACKOUT CREATE (🔥 ADDED)
# -----------------------------
class CreateBlackoutRequest(BaseModel):
    start_ts: datetime
    end_ts: datetime
    reason: str


# -----------------------------
# RESPONSE
# -----------------------------
class VehicleResponse(BaseModel):
    id: UUID
    vehicle_code: str
    vin: Optional[str]
    reg_no: str

    make: Optional[str]
    model: str
    variant: Optional[str]
    model_year: Optional[int]
    color: Optional[str]

    seating_capacity: int
    transmission: TransmissionType
    energy_type: VehicleEnergyType

    battery_capacity_kwh: Optional[Decimal]
    certified_range_km: Optional[int]
    battery_health_status: Optional[BatteryHealthStatus]

    operating_city_id: Optional[UUID]
    home_zone_id: Optional[UUID]
    telematics_device_id: Optional[UUID]

    cleanliness_status: CleanlinessStatus
    odometer_km_baseline: Optional[Decimal]
    notes: Optional[str]

    status: VehicleStatus
    is_deleted: bool

    class Config:
        from_attributes = True
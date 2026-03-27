# app/controllers/vehicle/update_vehicle.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.db.schema import Vehicle
from app.schemas.vehicle_schema import VehicleUpdateRequest, VehicleResponse

router = APIRouter(prefix="/admin/updatevehicles", tags=["Vehicle"])


# ✅ Only allow safe fields to be updated
ALLOWED_UPDATE_FIELDS = {
    "make", "model", "variant", "model_year", "color",
    "seating_capacity", "transmission", "energy_type",
    "battery_capacity_kwh", "certified_range_km",
    "battery_health_status",
    "operating_city_id", "home_zone_id", "telematics_device_id",
    "cleanliness_status", "odometer_km_baseline", "notes"
}


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdateRequest,
    db: Session = Depends(get_db)
):
    # ✅ Fetch vehicle (only non-deleted)
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.is_deleted.is_(False)   # cleaner SQLAlchemy style
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # ✅ Extract only provided fields
    update_data = payload.dict(exclude_unset=True)

    # ✅ Prevent empty update
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    # ✅ Apply updates safely
    for key, value in update_data.items():
        if key in ALLOWED_UPDATE_FIELDS:
            setattr(vehicle, key, value)

    # ✅ Save changes
    db.commit()
    db.refresh(vehicle)

    return vehicle
# app/services/vehicle/blackout_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID

from app.db.schema import VehicleBlackoutWindow, Vehicle, User


def is_vehicle_in_blackout(db: Session, vehicle_id: UUID, start, end) -> bool:
    """
    Check if the vehicle already has a blackout overlapping the given time window.
    """
    blackout = db.query(VehicleBlackoutWindow).filter(
        VehicleBlackoutWindow.vehicle_id == vehicle_id,
        VehicleBlackoutWindow.start_ts < end,
        VehicleBlackoutWindow.end_ts > start
    ).first()

    return blackout is not None


def create_blackout(db: Session, vehicle_id: UUID, payload) -> VehicleBlackoutWindow:
    """
    Create a new blackout window for a vehicle.
    Automatically fetches an admin user ID from the users table (user_type='ADMIN').

    :param db: SQLAlchemy session
    :param vehicle_id: UUID of the vehicle
    :param payload: CreateBlackoutRequest Pydantic object
    :return: VehicleBlackoutWindow object
    """

    # 1️⃣ Check vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # 2️⃣ Validate time
    if payload.end_ts <= payload.start_ts:
        raise HTTPException(status_code=400, detail="end_ts must be greater than start_ts")

    # 3️⃣ Check overlap
    if is_vehicle_in_blackout(db, vehicle_id, payload.start_ts, payload.end_ts):
        raise HTTPException(status_code=400, detail="Blackout already exists in this time range")

    # 4️⃣ Fetch admin user ID from users table
    admin_user = db.query(User).filter(User.user_type == 'ADMIN').first()
    if not admin_user:
        raise HTTPException(status_code=500, detail="No admin user found to assign blackout")

    # 5️⃣ Create blackout with admin_user_id
    blackout = VehicleBlackoutWindow(
        vehicle_id=vehicle_id,
        start_ts=payload.start_ts,
        end_ts=payload.end_ts,
        reason=payload.reason,
        created_by_user_id=admin_user.id  # ✅ assign admin ID
    )

    db.add(blackout)
    db.commit()
    db.refresh(blackout)

    return blackout
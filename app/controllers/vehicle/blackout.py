# app/controllers/vehicle/blackout.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.schemas.vehicle_schema import CreateBlackoutRequest  # ✅ fixed import
from app.services.vehicle.blackout_service import create_blackout

router = APIRouter()


@router.post("/vehicles/{vehicle_id}/blackout")
def create_blackout_api(
    vehicle_id: UUID,
    payload: CreateBlackoutRequest,
    db: Session = Depends(get_db)
):
    blackout = create_blackout(db, vehicle_id, payload)

    return {
        "message": "Blackout created successfully",
        "blackout_id": blackout.id
    }
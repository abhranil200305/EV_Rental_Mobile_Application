# app/controllers/vehicle/delete_vehicle.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.db.schema import Vehicle

router = APIRouter(prefix="/admin/deletevehicles", tags=["Vehicle"])


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: UUID, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.is_deleted.is_(False)   # ✅ better
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # ✅ Soft delete
    vehicle.is_deleted = True

    db.commit()
    db.refresh(vehicle)   # ✅ optional but good

    return {
        "message": "Vehicle deleted successfully",
        "vehicle_id": str(vehicle.id)   # ✅ helpful for frontend
    }
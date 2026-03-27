#app/controllers/vehicle/get_vehicle.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.schema import Vehicle
from app.schemas.vehicle_schema import VehicleResponse

router = APIRouter(prefix="/admin/vehicles", tags=["Vehicle"])


@router.get("/", response_model=List[VehicleResponse])
def get_all_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).filter(Vehicle.is_deleted == False).all()
    return vehicles


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: UUID, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.is_deleted == False
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return vehicle
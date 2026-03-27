#app/controllers/vehicle/create_vehicle.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schema import Vehicle
from app.schemas.vehicle_schema import VehicleCreateRequest, VehicleResponse

router = APIRouter(prefix="/admin/createvehicles", tags=["Vehicle"])


@router.post("/", response_model=VehicleResponse)
def create_vehicle(
    payload: VehicleCreateRequest,
    db: Session = Depends(get_db)
):
    # check uniqueness
    existing = db.query(Vehicle).filter(
        (Vehicle.vehicle_code == payload.vehicle_code) |
        (Vehicle.reg_no == payload.reg_no)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Vehicle already exists")

    vehicle = Vehicle(**payload.dict())

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return vehicle
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.vehicle import VehicleRequest, VehicleResponse
from app.services.vehicles import VehicleService
from app.utils.security import get_current_user, RoleChecker

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])

# Role guards
auth_guard = get_current_user
write_guard = RoleChecker(["OWNER", "MANAGER"])

@router.get("", response_model=List[VehicleResponse])
def get_all_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    return VehicleService.get_all_vehicles(db)

@router.post("", response_model=VehicleResponse)
def create_vehicle(
    request_data: VehicleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(write_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    return VehicleService.create_vehicle(
        db, 
        request_data, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )

@router.put("/{id}", response_model=VehicleResponse)
def update_vehicle(
    id: int,
    request_data: VehicleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(write_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    return VehicleService.update_vehicle(
        db, 
        id, 
        request_data, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(write_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    VehicleService.delete_vehicle(
        db, 
        id, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )

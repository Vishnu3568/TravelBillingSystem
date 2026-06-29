from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleRequest
from app.services.audit_log import AuditLogService

class VehicleService:
    @staticmethod
    def get_all_vehicles(db: Session) -> List[Vehicle]:
        return db.query(Vehicle).all()

    @staticmethod
    def create_vehicle(db: Session, request: VehicleRequest, current_user: str, current_role: str, ip: str) -> Vehicle:
        vehicle = Vehicle(
            registration_number=request.registrationNumber.strip(),
            type=request.type,
            model=request.model
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

        AuditLogService.log_action(
            db=db,
            action="CREATE_VEHICLE",
            module="VEHICLE",
            description=f"Created vehicle: {vehicle.registration_number}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )
        return vehicle

    @staticmethod
    def update_vehicle(db: Session, vehicle_id: int, request: VehicleRequest, current_user: str, current_role: str, ip: str) -> Vehicle:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )

        vehicle.registration_number = request.registrationNumber.strip()
        vehicle.type = request.type
        vehicle.model = request.model

        db.commit()
        db.refresh(vehicle)

        AuditLogService.log_action(
            db=db,
            action="UPDATE_VEHICLE",
            module="VEHICLE",
            description=f"Updated vehicle: {vehicle.registration_number}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )
        return vehicle

    @staticmethod
    def delete_vehicle(db: Session, vehicle_id: int, current_user: str, current_role: str, ip: str):
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )

        reg = vehicle.registration_number
        db.delete(vehicle)
        db.commit()

        AuditLogService.log_action(
            db=db,
            action="DELETE_VEHICLE",
            module="VEHICLE",
            description=f"Deleted vehicle: {reg}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )

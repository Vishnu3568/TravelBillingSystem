from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.user import UserRequest, UserResponse
from app.schemas.auth import PasswordResetRequest
from app.services.users import UserService
from app.utils.security import RoleChecker

router = APIRouter(prefix="/api/users", tags=["users"])

# All routes in this router require OWNER role
owner_guard = RoleChecker(["OWNER"])

@router.get("", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    return UserService.get_all_users(db)

@router.post("", response_model=UserResponse)
def create_user(
    request_data: UserRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    return UserService.create_user(
        db, 
        request_data, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )

@router.put("/{id}", response_model=UserResponse)
def update_user(
    id: int,
    request_data: UserRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    return UserService.update_user(
        db, 
        id, 
        request_data, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )

@router.put("/{id}/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    id: int,
    request_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    UserService.reset_password(
        db, 
        id, 
        request_data, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )
    return {"message": "Password reset successfully"}

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_user(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    UserService.delete_user(
        db, 
        id, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )
    return {"message": "User disabled/deleted successfully"}

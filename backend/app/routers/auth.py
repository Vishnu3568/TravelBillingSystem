from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.utils.security import RoleChecker, hash_password
from app.config import settings
from typing import Dict, Any

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(request_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    return AuthService.login(db, request_data, ip)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    request_data: RegisterRequest, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(RoleChecker(["OWNER"]))
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    user = AuthService.register(
        db, 
        request_data, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }

# Dev Auth Debug endpoints (enabled only under dev mode/profile)
@router.get("/debug/hash/{password}", response_model=str)
def hash_password_debug(password: str):
    if not settings.is_dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return hash_password(password)

@router.post("/debug/register-owner", status_code=status.HTTP_201_CREATED)
def register_owner_debug(request: Request, db: Session = Depends(get_db)):
    if not settings.is_dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
        
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    
    register_req = RegisterRequest(
        username="owner2",
        password="admin123",
        email="owner2@test.com",
        role="OWNER"
    )
    
    user = AuthService.register(db, register_req, "SYSTEM", "SYSTEM", ip)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.company import CompanyRequest, CompanyResponse
from app.services.companies import CompanyService
from app.utils.security import get_current_user, RoleChecker

router = APIRouter(prefix="/api/companies", tags=["companies"])

# Role guards
auth_guard = get_current_user
write_guard = RoleChecker(["OWNER", "MANAGER"])

@router.get("", response_model=List[CompanyResponse])
def get_all_companies(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    return CompanyService.get_all_companies(db)

@router.post("", response_model=CompanyResponse)
def create_company(
    request_data: CompanyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(write_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    return CompanyService.create_company(
        db, 
        request_data, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )

@router.put("/{id}", response_model=CompanyResponse)
def update_company(
    id: int,
    request_data: CompanyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(write_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    return CompanyService.update_company(
        db, 
        id, 
        request_data, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(write_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    CompanyService.delete_company(
        db, 
        id, 
        current_user.get("sub"), 
        current_user.get("role"), 
        ip
    )

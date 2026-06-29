from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app.models.company import Company
from app.schemas.company import CompanyRequest
from app.services.audit_log import AuditLogService

class CompanyService:
    @staticmethod
    def get_all_companies(db: Session) -> List[Company]:
        return db.query(Company).all()

    @staticmethod
    def create_company(db: Session, request: CompanyRequest, current_user: str, current_role: str, ip: str) -> Company:
        gst_num = request.gstNumber if request.hasGst else None
        company = Company(
            name=request.name.strip(),
            address=request.address,
            gst_number=gst_num
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        AuditLogService.log_action(
            db=db,
            action="CREATE_COMPANY",
            module="COMPANY",
            description=f"Created company: {company.name}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )
        return company

    @staticmethod
    def update_company(db: Session, company_id: int, request: CompanyRequest, current_user: str, current_role: str, ip: str) -> Company:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        company.name = request.name.strip()
        company.address = request.address
        company.gst_number = request.gstNumber if request.hasGst else None

        db.commit()
        db.refresh(company)

        AuditLogService.log_action(
            db=db,
            action="UPDATE_COMPANY",
            module="COMPANY",
            description=f"Updated company: {company.name}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )
        return company

    @staticmethod
    def delete_company(db: Session, company_id: int, current_user: str, current_role: str, ip: str):
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        name = company.name
        db.delete(company)
        db.commit()

        AuditLogService.log_action(
            db=db,
            action="DELETE_COMPANY",
            module="COMPANY",
            description=f"Deleted company: {name}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )

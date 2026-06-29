from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.services.audit_log import AuditLogService
from app.utils.security import RoleChecker
from app.routers.bills import make_page_response

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])

# Audit log route restricted to OWNER
owner_guard = RoleChecker(["OWNER"])

@router.get("")
def get_logs(
    username: Optional[str] = None,
    action: Optional[str] = None,
    startDate: Optional[datetime] = None,
    endDate: Optional[datetime] = None,
    page: int = 0,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    items, total = AuditLogService.get_logs(
        db, 
        username=username, 
        action=action, 
        start_date=startDate, 
        end_date=endDate, 
        page=page, 
        size=size
    )
    
    # Serialize logs (Pydantic / plain dict)
    # Fields: id, username, role, action, module, description, ipAddress (camelCase mapping), createdAt
    serialized = []
    for a in items:
        serialized.append({
            "id": a.id,
            "username": a.username,
            "role": a.role,
            "action": a.action,
            "module": a.module,
            "description": a.description,
            "ipAddress": a.ip_address,
            "createdAt": a.created_at.strftime("%Y-%m-%dT%H:%M:%S") if a.created_at else None
        })
        
    return make_page_response(serialized, total, page, size)

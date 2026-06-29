from sqlalchemy.orm import Session
from datetime import datetime
from app.models.audit_log import AuditLog

class AuditLogService:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        module: str,
        description: str,
        username: str = "SYSTEM",
        role: str = "SYSTEM",
        ip_address: str = ""
    ):
        log_entry = AuditLog(
            username=username,
            role=role,
            action=action,
            module=module,
            description=description,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

    @staticmethod
    def get_logs(
        db: Session,
        username: str = None,
        action: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = 0,
        size: int = 20
    ):
        query = db.query(AuditLog)
        
        if username:
            query = query.filter(AuditLog.username.like(f"%{username}%"))
        if action:
            query = query.filter(AuditLog.action == action)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
            
        # Order by created_at desc (matches Java Sort.Direction.DESC)
        query = query.order_by(AuditLog.created_at.desc())
        
        # Paginate
        total = query.count()
        items = query.offset(page * size).limit(size).all()
        
        return items, total

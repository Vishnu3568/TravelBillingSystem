from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    action = Column(String(255), nullable=True)
    module = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    ip_address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    address = Column(String(255), nullable=True)
    gst_number = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    @property
    def gstNumber(self):
        return self.gst_number

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    bills = relationship("Bill", back_populates="company")


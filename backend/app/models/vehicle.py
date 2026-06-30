from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String(255), unique=True, index=True, nullable=False)
    type = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    @property
    def registrationNumber(self):
        return self.registration_number

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    bills = relationship("Bill", back_populates="vehicle")


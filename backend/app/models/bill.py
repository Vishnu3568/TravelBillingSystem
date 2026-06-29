from sqlalchemy import Column, Integer, String, Double, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    bill_number = Column(String(255), unique=True, index=True, nullable=False)
    amount = Column(Double, nullable=True)
    bill_date = Column(DateTime, nullable=True)
    company_name = Column(String(255), nullable=True)
    vehicle_name = Column(String(255), nullable=True)
    duty_slip_no = Column(String(255), nullable=True)
    trip_date = Column(DateTime, nullable=True)
    vehicle_type = Column(String(255), nullable=True)
    ac_non_ac = Column(String(255), nullable=True)
    total_kms = Column(Double, nullable=True)
    total_hours = Column(Double, nullable=True)
    extra_kms = Column(Double, nullable=True)
    extra_hours = Column(Double, nullable=True)
    trip_type = Column(String(255), nullable=True)
    pricing_type = Column(String(255), nullable=True)
    base_amount = Column(Double, nullable=True)
    driver_bata = Column(Double, nullable=True)
    parking = Column(Double, nullable=True)
    toll = Column(Double, nullable=True)
    night_charges = Column(Double, nullable=True)
    other_charges = Column(Double, nullable=True)
    notes = Column(String(1000), nullable=True)
    dynamic_charges = Column(Text, nullable=True)
    contact_person = Column(String(255), nullable=True)
    booked_by = Column(String(255), nullable=True)
    manager_name = Column(String(255), nullable=True)
    grand_total = Column(Double, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    company = relationship("Company", back_populates="bills")

    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    vehicle = relationship("Vehicle", back_populates="bills")

    payments = relationship("Payment", back_populates="bill", cascade="all, delete-orphan")

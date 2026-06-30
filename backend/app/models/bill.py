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

    @property
    def billNumber(self):
        return self.bill_number

    @property
    def billDate(self):
        return self.bill_date

    @property
    def companyName(self):
        return self.company_name

    @property
    def vehicleName(self):
        return self.vehicle_name

    @property
    def dutySlipNo(self):
        return self.duty_slip_no

    @property
    def tripDate(self):
        return self.trip_date

    @property
    def vehicleType(self):
        return self.vehicle_type

    @property
    def acNonAc(self):
        return self.ac_non_ac

    @property
    def totalKms(self):
        return self.total_kms

    @property
    def totalHours(self):
        return self.total_hours

    @property
    def extraKms(self):
        return self.extra_kms

    @property
    def extraHours(self):
        return self.extra_hours

    @property
    def tripType(self):
        return self.trip_type

    @property
    def pricingType(self):
        return self.pricing_type

    @property
    def baseAmount(self):
        return self.base_amount

    @property
    def driverBata(self):
        return self.driver_bata

    @property
    def nightCharges(self):
        return self.night_charges

    @property
    def otherCharges(self):
        return self.other_charges

    @property
    def contactPerson(self):
        return self.contact_person

    @property
    def bookedBy(self):
        return self.booked_by

    @property
    def managerName(self):
        return self.manager_name

    @property
    def grandTotal(self):
        return self.grand_total

    @property
    def createdBy(self):
        return self.created_by

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @property
    def dynamicCharges(self):
        if not self.dynamic_charges:
            return []
        import json
        try:
            return json.loads(self.dynamic_charges)
        except Exception:
            return []

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    company = relationship("Company", back_populates="bills")

    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    vehicle = relationship("Vehicle", back_populates="bills")

    payments = relationship("Payment", back_populates="bill", cascade="all, delete-orphan")


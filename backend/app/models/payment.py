from sqlalchemy import Column, Integer, Double, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Double, nullable=True)
    payment_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    @property
    def paymentDate(self):
        return self.payment_date

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @property
    def billId(self):
        return self.bill_id

    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=True)
    bill = relationship("Bill", back_populates="payments")


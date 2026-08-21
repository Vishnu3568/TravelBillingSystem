from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class ChargeDTO(BaseModel):
    name: str
    description: Optional[str] = None
    amount: float

class BillRequest(BaseModel):
    billDate: date
    companyName: str
    vehicleName: str
    dutySlipNo: str
    tripDate: Optional[date] = None
    vehicleType: Optional[str] = None
    acNonAc: Optional[str] = None
    totalKms: Optional[float] = 0.0
    totalHours: Optional[float] = 0.0
    extraKms: Optional[float] = 0.0
    extraHours: Optional[float] = 0.0
    tripType: Optional[str] = None
    pricingType: Optional[str] = None
    baseAmount: Optional[float] = 0.0
    driverBata: Optional[float] = 0.0
    parking: Optional[float] = 0.0
    toll: Optional[float] = 0.0
    nightCharges: Optional[float] = 0.0
    otherCharges: Optional[float] = 0.0
    dynamicCharges: Optional[List[ChargeDTO]] = None
    notes: Optional[str] = None
    contactPerson: Optional[str] = None
    bookedBy: Optional[str] = None
    managerName: Optional[str] = None
    rawValues: Optional[str] = None
    originalDoc: Optional[str] = None

class BillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    billNumber: str
    billDate: Optional[date] = None
    companyName: Optional[str] = None
    vehicleName: Optional[str] = None
    dutySlipNo: Optional[str] = None
    tripDate: Optional[date] = None
    vehicleType: Optional[str] = None
    acNonAc: Optional[str] = None
    totalKms: Optional[float] = 0.0
    totalHours: Optional[float] = 0.0
    extraKms: Optional[float] = 0.0
    extraHours: Optional[float] = 0.0
    tripType: Optional[str] = None
    pricingType: Optional[str] = None
    baseAmount: Optional[float] = 0.0
    driverBata: Optional[float] = 0.0
    parking: Optional[float] = 0.0
    toll: Optional[float] = 0.0
    nightCharges: Optional[float] = 0.0
    otherCharges: Optional[float] = 0.0
    dynamicCharges: Optional[List[ChargeDTO]] = None
    notes: Optional[str] = None
    grandTotal: Optional[float] = 0.0
    createdBy: Optional[str] = None
    createdAt: Optional[datetime] = None
    contactPerson: Optional[str] = None
    bookedBy: Optional[str] = None
    managerName: Optional[str] = None
    rawValues: Optional[str] = None
    originalDoc: Optional[str] = None

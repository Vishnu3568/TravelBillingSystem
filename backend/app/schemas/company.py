from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CompanyRequest(BaseModel):
    name: str
    address: Optional[str] = None
    gstNumber: Optional[str] = None
    hasGst: Optional[bool] = None

class CompanyResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    gstNumber: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True

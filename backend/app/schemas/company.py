from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CompanyRequest(BaseModel):
    name: str
    address: Optional[str] = None
    gstNumber: Optional[str] = None
    hasGst: Optional[bool] = None

class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: Optional[str] = None
    gstNumber: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

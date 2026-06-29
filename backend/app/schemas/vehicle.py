from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VehicleRequest(BaseModel):
    registrationNumber: str
    type: Optional[str] = None
    model: Optional[str] = None

class VehicleResponse(BaseModel):
    id: int
    registrationNumber: str
    type: Optional[str] = None
    model: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True

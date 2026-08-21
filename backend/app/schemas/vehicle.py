from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class VehicleRequest(BaseModel):
    registrationNumber: str
    type: Optional[str] = None
    model: Optional[str] = None

class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registrationNumber: str
    type: Optional[str] = None
    model: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

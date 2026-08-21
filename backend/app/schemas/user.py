from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class UserRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    fullName: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    fullName: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    active: bool
    createdAt: Optional[datetime] = None

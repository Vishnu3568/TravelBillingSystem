from pydantic import BaseModel
from datetime import datetime

class BackupResponse(BaseModel):
    fileName: str
    size: int
    createdAt: datetime

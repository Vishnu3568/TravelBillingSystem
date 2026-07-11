from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CopilotChatRequest(BaseModel):
    query: str
    sessionId: str
    billId: Optional[int] = None

class CopilotChatResponse(BaseModel):
    answer: str
    confidence: float
    references: List[str] = Field(default_factory=list)
    action: Optional[Dict[str, Any]] = None

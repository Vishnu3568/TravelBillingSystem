from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.services.document_intelligence.document_models import DocumentMetadata

class LabeledElement(BaseModel):
    id: str
    text: str
    coordinates: Dict[str, Any] = Field(default_factory=dict)
    formatting: Dict[str, Any] = Field(default_factory=dict)
    label: str
    confidence: float

class LabeledDocument(BaseModel):
    metadata: DocumentMetadata
    elements: List[LabeledElement] = Field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)

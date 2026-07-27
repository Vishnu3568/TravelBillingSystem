"""
AMIP Evidence Context Model.
Stores raw evidence, OCR structures, metadata, and cross-engine knowledge facts.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List


@dataclass
class EvidenceContext:
    """
    Holds all raw and derived evidence for an execution context task.
    """
    raw_document: Optional[bytes] = None
    ocr_text: str = ""
    uploaded_filename: str = ""
    document_metadata: Dict[str, Any] = field(default_factory=dict)
    bill_metadata: Dict[str, Any] = field(default_factory=dict)
    knowledge_context: List[str] = field(default_factory=list)
    graph_context: Dict[str, Any] = field(default_factory=dict)
    learning_context: Dict[str, Any] = field(default_factory=dict)
    predictive_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_raw_bytes: bool = False) -> Dict[str, Any]:
        """
        Serializes the evidence context to a dictionary.
        Optionally excludes raw binary document bytes for clean JSON serialization.
        """
        data = asdict(self)
        if not include_raw_bytes:
            data["raw_document"] = f"<{len(self.raw_document)} bytes>" if self.raw_document else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceContext:
        """Constructs an EvidenceContext instance from a dictionary."""
        raw_doc = data.get("raw_document")
        if isinstance(raw_doc, str) and raw_doc.startswith("<") and raw_doc.endswith(">"):
            raw_doc = None

        return cls(
            raw_document=raw_doc if isinstance(raw_doc, bytes) else None,
            ocr_text=data.get("ocr_text", ""),
            uploaded_filename=data.get("uploaded_filename", ""),
            document_metadata=dict(data.get("document_metadata", {})),
            bill_metadata=dict(data.get("bill_metadata", {})),
            knowledge_context=list(data.get("knowledge_context", [])),
            graph_context=dict(data.get("graph_context", {})),
            learning_context=dict(data.get("learning_context", {})),
            predictive_context=dict(data.get("predictive_context", {})),
        )

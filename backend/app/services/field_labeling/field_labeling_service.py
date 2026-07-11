from __future__ import annotations

from typing import Dict, Any
from app.services.document_intelligence.document_models import EnterpriseDocument
from app.services.field_labeling.field_models import LabeledDocument
from app.services.field_labeling.labeling_orchestrator import LabelingOrchestrator
from app.services.field_labeling.label_mapper import LabelMapper

class FieldLabelingService:
    @staticmethod
    def label_document(doc: EnterpriseDocument, learned_context: str = "") -> LabeledDocument:
        """
        Public API: processes the structured document representation, batch labels it
        via LLM or local fallback classifier, filters by confidence, and returns LabeledDocument.
        """
        return LabelingOrchestrator.orchestrate_labeling(doc, learned_context)

    @staticmethod
    def map_to_parser_dict(labeled_doc: LabeledDocument) -> Dict[str, Any]:
        """
        Converts the labeled document back to the standard 26-field parser format.
        """
        return LabelMapper.to_extraction_dict(labeled_doc)

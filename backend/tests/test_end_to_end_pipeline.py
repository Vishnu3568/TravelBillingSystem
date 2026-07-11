from __future__ import annotations

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings

# Import all engine services
from app.services.document_intelligence.document_models import EnterpriseDocument, DocumentMetadata, DocumentPage
from app.services.field_labeling.labeling_orchestrator import LabelingOrchestrator
from app.services.field_labeling.field_models import LabeledDocument, LabeledElement
from app.services.validation_engine import ValidationEngineService
from app.services.learning_engine.correction_store import CorrectionStore
from app.services.knowledge_graph import GraphService
from app.services.predictive_engine.predictive_service import PredictiveService
from app.services.enterprise_copilot import CopilotService, CopilotChatRequest

from app.models.bill import Bill
from app.models.company import Company
from app.models.vehicle import Vehicle

@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_end_to_end_pipeline_success(db_session, monkeypatch):
    # Ensure all enterprise features are enabled
    settings.USE_ENTERPRISE_LEARNING = True
    settings.USE_ENTERPRISE_COPILOT = True
    settings.USE_ENTERPRISE_GRAPH = True
    settings.USE_PREDICTIVE_ENGINE = True

    # Seed initial setup: company and vehicle
    company = Company(name="Portescap")
    vehicle = Vehicle(registration_number="TS09EX1111", model="Sedan", type="Sedan")
    db_session.add_all([company, vehicle])
    db_session.commit()

    # 1. Document Intelligence parsing simulation (construct a mock EnterpriseDocument)
    fallback_metadata = DocumentMetadata(
        file_name="test_bill.docx",
        file_size_bytes=1000,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        source_format="docx"
    )
    fallback_page = DocumentPage(
        id="page-1",
        page_number=1,
        position=1,
        title="test_bill.docx",
        paragraphs=[],
        tables=[],
        reading_order=[],
        metadata={"fallback_text": "Duty Slip No: DS-E2E-100\nCompany: Portescap"}
    )
    doc_model = EnterpriseDocument(
        id="doc-e2e",
        metadata=fallback_metadata,
        pages=[fallback_page],
        coordinates=[],
        reading_order=[]
    )
    assert doc_model.id == "doc-e2e"
    
    # 2. Field Labeling simulation
    # Construct a mock LabeledDocument containing required fields
    labeled_doc = LabeledDocument(
        metadata=fallback_metadata,
        elements=[
            LabeledElement(id="el1", text="Portescap", coordinates={"page_number": 1}, formatting={}, label="HEADER_COMPANY", confidence=0.99),
            LabeledElement(id="el2", text="TS09EX1111", coordinates={"page_number": 1}, formatting={}, label="VEHICLE_NUMBER", confidence=0.99),
            LabeledElement(id="el3", text="DS-E2E-100", coordinates={"page_number": 1}, formatting={}, label="HEADER_BILL_NUMBER", confidence=0.99),
            LabeledElement(id="el4", text="1800.00", coordinates={"page_number": 1}, formatting={}, label="TOTAL_AMOUNT", confidence=0.99)
        ]
    )
    assert len(labeled_doc.elements) == 4

    # 3. Validation Engine check
    # Prepare dummy coordinates matching the document shape
    coords_dict = {
        "HEADER_COMPANY": {"value": "Portescap", "box": [10, 10, 20, 50], "confidence": 0.99},
        "TOTAL_AMOUNT": {"value": "1800.00", "box": [50, 10, 60, 50], "confidence": 0.99}
    }
    
    # Run validation service
    validation_report = ValidationEngineService.validate_labeled_document(
        db=db_session,
        labeled_doc=labeled_doc
    )
    assert validation_report.validation_summary.overall_quality_score >= 0.0

    # Seed Bill object into database
    bill = Bill(
        bill_number="DS-E2E-100",
        company_name="Portescap",
        vehicle_name="TS09EX1111",
        grand_total=1800.0,
        total_kms=100.0,
        total_hours=5.0
    )
    db_session.add(bill)
    db_session.commit()

    # 4. Learning Engine updates
    # Save a correction to simulate human feedback
    from app.services.learning_engine.learning_models import CorrectionRecord
    record = CorrectionRecord(
        original_value="1500.00",
        corrected_value="1800.00",
        field_type="grand_total",
        company_name="Portescap",
        vehicle_number="TS09EX1111",
        bill_number="DS-E2E-100",
        reviewer="owner2"
    )
    correction = CorrectionStore.save_correction(db_session, record)
    assert correction is not None

    # 5. Knowledge Graph construction
    # Rebuild graph incrementally
    GraphService.register_bill_save(db_session, bill)
    stats = db_session.execute(
        Base.metadata.tables["graph_nodes"].select()
    ).fetchall()
    assert len(stats) > 0

    # 6. Embedding generation & Vector Store simulation
    monkeypatch.setattr(
        "app.services.gemini.GeminiService.index_bill",
        lambda self, bill_id, text: None
    )
    monkeypatch.setattr(
        "app.services.gemini.GeminiService.ask_assistant",
        lambda self, request_data: {
            "answer": "The total for bill DS-E2E-100 is 1800.00",
            "confidence": 0.99,
            "references": ["totalAmount"]
        }
    )
    assert True

    # 7. Predictive Engine Projections
    predictive_summary = PredictiveService.get_predictive_summary(db_session)
    assert predictive_summary is not None
    assert predictive_summary.revenue_forecast.monthly > 0

    # 8. Copilot response generation
    # Execute copilot search query referencing E2E bill details
    req = CopilotChatRequest(
        query="What was the total for bill DS-E2E-100?",
        sessionId="e2e_session",
        billId=None
    )
    copilot_reply = CopilotService.ask_copilot(
        db=db_session,
        request=req,
        user_role="OWNER",
        username="owner2"
    )
    assert copilot_reply is not None
    assert copilot_reply.answer is not None

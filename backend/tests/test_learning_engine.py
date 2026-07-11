from __future__ import annotations

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings
from app.schemas.ai import AiBillResponse, AiBillCharge
from app.services.field_labeling.field_models import LabeledDocument, LabeledElement
from app.services.document_intelligence.document_models import DocumentMetadata

# Import Learning Engine Modules
from app.services.learning_engine.learning_models import CorrectionRecord
from app.services.learning_engine.correction_store import CorrectionStore
from app.services.learning_engine.pattern_engine import PatternEngine
from app.services.learning_engine.company_learning import CompanyLearning
from app.services.learning_engine.vehicle_learning import VehicleLearning
from app.services.learning_engine.confidence_learning import ConfidenceLearning
from app.services.learning_engine.feedback_processor import FeedbackProcessor
from app.services.learning_engine.knowledge_store import KnowledgeStore
from app.services.learning_engine.learning_statistics import LearningStatistics
from app.services.learning_engine.knowledge_export import KnowledgeExport
from app.services.learning_engine.learning_service import LearningService

# Setup in-memory sqlite for learning engine testing
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

def test_correction_store_versioning(db_session):
    # Create first correction
    record = CorrectionRecord(
        original_value="Original Company A",
        corrected_value="Corrected Company B",
        field_type="companyName",
        table_number=1,
        row_index=0,
        column_index=1,
        company_name="Company B",
        vehicle_number="TS-09-UB-8888",
        bill_number="BILL-999",
        reviewer="owner2",
        reason="Manual adjustment",
        ai_confidence=0.88,
        validation_status="EDITED"
    )
    
    corr1 = CorrectionStore.save_correction(db_session, record)
    assert corr1.version == 1
    assert corr1.correction_count == 1
    assert corr1.original_value == "Original Company A"
    assert corr1.corrected_value == "Corrected Company B"

    # Create second correction for the same field + company + vehicle combo
    corr2 = CorrectionStore.save_correction(db_session, record)
    assert corr2.version == 2
    assert corr2.correction_count == 2
    assert corr2.original_value == "Original Company A"
    assert corr2.corrected_value == "Corrected Company B"

def test_pattern_engine_spatial_relations():
    metadata = DocumentMetadata(file_name="test_bill.docx")
    elements = [
        # Booked By at row 0, col 1
        LabeledElement(id="el1", text="Kumar", coordinates={"table_number": 1, "row_index": 0, "column_index": 1}, formatting={}, label="BOOKED_BY", confidence=0.99),
        # Guest Name at row 1, col 1 (immediately under Booked By)
        LabeledElement(id="el2", text="Rajesh", coordinates={"table_number": 1, "row_index": 1, "column_index": 1}, formatting={}, label="GUEST_NAME", confidence=0.95),
        # Vehicle Type beside Vehicle Number on row 2
        LabeledElement(id="el3", text="SUV", coordinates={"table_number": 1, "row_index": 2, "column_index": 0}, formatting={}, label="VEHICLE_TYPE", confidence=0.99),
        LabeledElement(id="el4", text="TS-09-UB-8888", coordinates={"table_number": 1, "row_index": 2, "column_index": 1}, formatting={}, label="VEHICLE_NUMBER", confidence=0.99),
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    relations = PatternEngine.extract_spatial_relationships(labeled_doc)
    assert len(relations) >= 3
    
    # Check 'below' relationship
    below_rel = next((r for r in relations if r["type"] == "below"), None)
    assert below_rel is not None
    assert below_rel["first_label"] == "GUEST_NAME"
    assert below_rel["second_label"] == "BOOKED_BY"

    # Check 'beside' relationship
    beside_rel = next((r for r in relations if r["type"] == "beside"), None)
    assert beside_rel is not None
    assert beside_rel["first_label"] == "VEHICLE_NUMBER"
    assert beside_rel["second_label"] == "VEHICLE_TYPE"

def test_company_learning_updates(db_session):
    metadata = DocumentMetadata(file_name="test_bill.docx")
    elements = [
        LabeledElement(id="el1", text="Portescap Co:", coordinates={"table_number": 1, "row_index": 0, "column_index": 1}, formatting={}, label="HEADER_COMPANY", confidence=0.90)
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)

    # Load / create profile
    profile = CompanyLearning.update_profile_from_document(db_session, "Portescap", labeled_doc, corrected_fields=["companyName"])
    assert profile.company_name == "Portescap"
    assert "HEADER_COMPANY" in profile.field_locations
    assert "Portescap Co:" in profile.preferred_labels
    assert "companyName" in profile.frequently_corrected_fields
    
    # Assert average confidence is calculated as moving average
    assert profile.average_confidence < 1.0

def test_vehicle_learning_layouts(db_session):
    metadata = DocumentMetadata(file_name="test_bill.docx")
    elements = [
        LabeledElement(id="el1", text="Sedan", coordinates={"table_number": 1, "row_index": 0, "column_index": 3}, formatting={}, label="VEHICLE_TYPE", confidence=0.99)
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    profile = VehicleLearning.update_profile_from_document(db_session, "Sedan", labeled_doc)
    assert profile.vehicle_type == "Sedan"
    structures = json.loads(profile.recurring_structures)
    assert "table_1" in structures
    assert structures["table_1"]["columns"] == 4

def test_confidence_learning_adaptive(db_session):
    # First Result: was_corrected = True (penalize confidence)
    c1 = ConfidenceLearning.record_prediction_result(db_session, "VEHICLE_NUMBER", was_corrected=True)
    assert c1.adaptive_confidence < 1.0
    assert c1.corrected_predictions_count == 1
    
    # Second Result: was_corrected = False (boost/reward)
    c2 = ConfidenceLearning.record_prediction_result(db_session, "VEHICLE_NUMBER", was_corrected=False)
    assert c2.correct_predictions_count == 1

def test_knowledge_retrieval_and_store(db_session):
    # Add dummy patterns/corrections for Company
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        LabeledElement(id="el1", text="Portescap Co:", coordinates={"table_number": 1, "row_index": 0, "column_index": 1}, formatting={}, label="HEADER_COMPANY", confidence=0.95)
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    CompanyLearning.update_profile_from_document(db_session, "Portescap", labeled_doc)
    
    context = KnowledgeStore.retrieve_learned_context(db_session, "Portescap", "Sedan")
    assert "Company: Portescap" in context
    assert "Preferred Header Labels" in context

def test_learning_statistics_and_analytics(db_session):
    FeedbackProcessor.process_reviewer_action(db_session, "owner2", "EDIT")
    FeedbackProcessor.process_reviewer_action(db_session, "owner2", "SAVE")
    
    stats = LearningStatistics.get_statistics(db_session)
    assert stats is not None
    assert stats.knowledge_base_size == 0 # no global rules added yet

def test_knowledge_export(db_session):
    json_data = KnowledgeExport.export_as_json(db_session)
    assert "companies" in json_data
    
    csv_data = KnowledgeExport.export_as_csv(db_session)
    assert "Type,Identifier,KeyName,ValueDetail" in csv_data

def test_feature_flags_and_facade(db_session):
    # Mock settings.USE_ENTERPRISE_LEARNING to false
    settings.USE_ENTERPRISE_LEARNING = False
    
    # Since it is false, get_learned_context should return empty string
    context = LearningService.get_learned_context(db_session, "Portescap")
    assert context == ""
    
    # Enable and test
    settings.USE_ENTERPRISE_LEARNING = True
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        LabeledElement(id="el1", text="Portescap Co:", coordinates={"table_number": 1, "row_index": 0, "column_index": 1}, formatting={}, label="HEADER_COMPANY", confidence=0.95)
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    CompanyLearning.update_profile_from_document(db_session, "Portescap", labeled_doc)
    
    context_enabled = LearningService.get_learned_context(db_session, "Portescap")
    assert "Company: Portescap" in context_enabled

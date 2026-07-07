from __future__ import annotations

import pytest
from app.services.document_intelligence.document_models import DocumentMetadata
from app.services.field_labeling.field_constants import FieldLabel
from app.services.field_labeling.field_models import LabeledDocument, LabeledElement
from app.services.validation_engine.validation_models import Severity, Recommendation, ValidationIssue
from app.services.validation_engine.coordinate_validator import CoordinateValidator
from app.services.validation_engine.label_validator import LabelValidator
from app.services.validation_engine.confidence_validator import ConfidenceValidator
from app.services.validation_engine.relationship_validator import RelationshipValidator
from app.services.validation_engine.formula_validator import FormulaValidator
from app.services.validation_engine.duplicate_detector import DuplicateDetector
from app.services.validation_engine.validation_report import ValidationReportGenerator
from app.services.validation_engine import ValidationEngineService

def test_coordinate_validator():
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        # Missing coordinates
        LabeledElement(id="el1", text="Portescap", coordinates={}, formatting={}, label="HEADER_COMPANY", confidence=0.99),
        # Invalid page number
        LabeledElement(id="el2", text="1234", coordinates={"page_number": 0}, formatting={}, label="HEADER_BILL_NUMBER", confidence=0.99),
        # Out-of-bound table index
        LabeledElement(id="el3", text="Sedan", coordinates={"page_number": 1, "table_number": 1, "row_index": -1, "column_index": 0}, formatting={}, label="VEHICLE_TYPE", confidence=0.99)
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    issues = CoordinateValidator.validate(labeled_doc)
    assert len(issues) == 3
    assert any(iss.rule_violated == "COORDINATE_MISSING" for iss in issues)
    assert any(iss.rule_violated == "INVALID_PAGE_COORDINATE" for iss in issues)
    assert any(iss.rule_violated == "INVALID_CELL_INDEXES" for iss in issues)

def test_label_validator():
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        # Allowed and correct
        LabeledElement(id="el1", text="STB/123", coordinates={"page_number": 1}, formatting={}, label="HEADER_BILL_NUMBER", confidence=0.99),
        # Duplicate billing number (unique field)
        LabeledElement(id="el2", text="STB/456", coordinates={"page_number": 1}, formatting={}, label="HEADER_BILL_NUMBER", confidence=0.99),
        # Invalid Enum Label
        LabeledElement(id="el3", text="Some text", coordinates={"page_number": 1}, formatting={}, label="SOME_INVALID_ENUM_X", confidence=0.99),
        # UNKNOWN label tracked
        LabeledElement(id="el4", text="Unknown detail", coordinates={"page_number": 1}, formatting={}, label="UNKNOWN", confidence=0.99)
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    issues = LabelValidator.validate(labeled_doc)
    assert len(issues) >= 4
    assert any(iss.rule_violated == "INVALID_LABEL_ENUM" for iss in issues)
    assert any(iss.rule_violated == "DUPLICATE_LABEL_ASSIGNMENT" for iss in issues)
    assert any(iss.rule_violated == "UNKNOWN_LABEL_ASSIGNMENT" for iss in issues)
    # Required fields missing errors (since we didn't provide duty slip, company, vehicle, total amount, etc.)
    assert any(iss.rule_violated == "MISSING_REQUIRED_LABEL" and iss.field == "HEADER_COMPANY" for iss in issues)

def test_confidence_validator():
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        LabeledElement(id="el1", text="TS08EX6458", coordinates={"page_number": 1}, formatting={}, label="VEHICLE_NUMBER", confidence=0.99), # Pass
        LabeledElement(id="el2", text="Sedan", coordinates={"page_number": 1}, formatting={}, label="VEHICLE_TYPE", confidence=0.96),         # Warning
        LabeledElement(id="el3", text="Portescap", coordinates={"page_number": 1}, formatting={}, label="HEADER_COMPANY", confidence=0.92),    # Error
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    issues = ConfidenceValidator.validate(labeled_doc)
    assert len(issues) == 2
    assert any(iss.rule_violated == "LOW_CONFIDENCE_WARNING" for iss in issues)
    assert any(iss.rule_violated == "LOW_CONFIDENCE_ERROR" for iss in issues)

def test_relationship_validator(db_session=None):
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        LabeledElement(id="el1", text="Authorised Signature", coordinates={"page_number": 1}, formatting={}, label="BOOKED_BY", confidence=0.99), # footer overlap error
        LabeledElement(id="el2", text="Sri Tulja Bhavani Travels", coordinates={"page_number": 1}, formatting={}, label="GUEST_NAME", confidence=0.99), # provider overlap error
        LabeledElement(id="el3", text="4940.00", coordinates={"page_number": 1}, formatting={}, label="TOTAL_AMOUNT", confidence=0.99),
        LabeledElement(id="el4", text="One Hundred Rupees Only", coordinates={"page_number": 1}, formatting={}, label="AMOUNT_WORDS", confidence=0.99) # amount mismatch
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    issues = RelationshipValidator.validate(db_session, labeled_doc)
    assert len(issues) == 3
    assert any(iss.rule_violated == "BOOKED_BY_FOOTER_OVERLAP" for iss in issues)
    assert any(iss.rule_violated == "GUEST_PROVIDER_OVERLAP" for iss in issues)
    assert any(iss.rule_violated == "AMOUNT_WORDS_MISMATCH" for iss in issues)

def test_formula_validator_and_arithmetic():
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        # Extra KM formula: 130x15 = 1950. But claimed extra KM amt is 1800. Mismatch!
        LabeledElement(id="el1", text="130x15", coordinates={"page_number": 1}, formatting={}, label="EXTRA_KM_FORMULA", confidence=0.99),
        LabeledElement(id="el2", text="1800.00", coordinates={"page_number": 1}, formatting={}, label="EXTRA_KM_AMOUNT", confidence=0.99),
        
        # Extra Hour formula: 3x150 = 450. Claimed extra hour amt is 450. Pass!
        LabeledElement(id="el3", text="3x150", coordinates={"page_number": 1}, formatting={}, label="EXTRA_HOUR_FORMULA", confidence=0.99),
        LabeledElement(id="el4", text="450.00", coordinates={"page_number": 1}, formatting={}, label="EXTRA_HOUR_AMOUNT", confidence=0.99),
        
        # Total check: base: 2500, bata: 300, toll: 150. Sum is 2500+300+150+1800+450 = 5200. But claimed total is 4940. Mismatch!
        LabeledElement(id="el5", text="2500.00", coordinates={"page_number": 1}, formatting={}, label="BASE_PACKAGE", confidence=0.99),
        LabeledElement(id="el6", text="300.00", coordinates={"page_number": 1}, formatting={}, label="DRIVER_BATA", confidence=0.99),
        LabeledElement(id="el7", text="150.00", coordinates={"page_number": 1}, formatting={}, label="TOLL", confidence=0.99),
        LabeledElement(id="el8", text="4940.00", coordinates={"page_number": 1}, formatting={}, label="TOTAL_AMOUNT", confidence=0.99),
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    issues = FormulaValidator.validate(labeled_doc)
    assert len(issues) == 2
    assert any(iss.rule_violated == "EXTRA_KM_FORMULA_MISMATCH" for iss in issues)
    assert any(iss.rule_violated == "GRAND_TOTAL_ARITHMETIC_MISMATCH" for iss in issues)

def test_validation_report_score_arithmetic():
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        LabeledElement(id="el1", text="STB/123", coordinates={"page_number": 1}, formatting={}, label="HEADER_BILL_NUMBER", confidence=0.98),
        LabeledElement(id="el2", text="Portescap", coordinates={"page_number": 1}, formatting={}, label="HEADER_COMPANY", confidence=0.98),
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    # 1 Error, 1 Warning, 1 Info
    issues = [
        ValidationIssue(field="HEADER_BILL_NUMBER", severity=Severity.ERROR, message="Err", rule_violated="R1"),
        ValidationIssue(field="HEADER_COMPANY", severity=Severity.WARNING, message="Warn", rule_violated="R2"),
        ValidationIssue(field="UNKNOWN", severity=Severity.INFO, message="Info", rule_violated="R3")
    ]
    
    report = ValidationReportGenerator.generate_report(labeled_doc, issues)
    
    # Deductions: 1 Error (15) + 1 Warning (5) + 1 Info (1) = 21. Score should be 100 - 21 = 79
    assert report.validation_summary.overall_quality_score == 79.0
    assert report.validation_summary.error_count == 1
    assert report.validation_summary.warning_count == 1
    assert report.validation_summary.info_count == 1
    # 1 Error -> Recommendation MANUAL_REVIEW since it's only 1 error and score > 70
    assert report.validation_summary.recommendation == Recommendation.MANUAL_REVIEW

def test_end_to_end_orchestration_facade():
    metadata = DocumentMetadata(file_name="test.docx")
    # A completely correct, valid document
    elements = [
        LabeledElement(id="el1", text="STB/2026/1", coordinates={"page_number": 1}, formatting={}, label="HEADER_BILL_NUMBER", confidence=0.99),
        LabeledElement(id="el2", text="DS-9041", coordinates={"page_number": 1}, formatting={}, label="HEADER_DUTY_SLIP", confidence=0.99),
        LabeledElement(id="el3", text="Portescap", coordinates={"page_number": 1}, formatting={}, label="HEADER_COMPANY", confidence=0.99),
        LabeledElement(id="el4", text="TS08EX6458", coordinates={"page_number": 1}, formatting={}, label="VEHICLE_NUMBER", confidence=0.99),
        LabeledElement(id="el5", text="Sedan A/C", coordinates={"page_number": 1}, formatting={}, label="VEHICLE_TYPE", confidence=0.99),
        LabeledElement(id="el6", text="22-10-2022", coordinates={"page_number": 1}, formatting={}, label="HEADER_DATE", confidence=0.99),
        LabeledElement(id="el7", text="2500.00", coordinates={"page_number": 1}, formatting={}, label="BASE_PACKAGE", confidence=0.99),
        LabeledElement(id="el8", text="2500.00", coordinates={"page_number": 1}, formatting={}, label="TOTAL_AMOUNT", confidence=0.99),
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    validated = ValidationEngineService.validate_labeled_document(None, labeled_doc)
    
    # Fully valid, so overall quality score should be 100
    assert validated.validation_summary.overall_quality_score == 100.0
    assert validated.validation_summary.error_count == 0
    assert validated.validation_summary.warning_count == 0
    assert validated.validation_summary.recommendation == Recommendation.PASS
    assert len(validated.issues) == 0

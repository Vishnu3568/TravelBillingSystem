from __future__ import annotations

import pytest
from app.services.document_intelligence.document_models import (
    DocumentCell,
    DocumentMetadata,
    DocumentPage,
    DocumentParagraph,
    DocumentRow,
    DocumentTable,
    EnterpriseDocument,
)
from app.services.field_labeling.field_constants import FieldLabel
from app.services.field_labeling.field_models import LabeledDocument, LabeledElement
from app.services.field_labeling.confidence_engine import ConfidenceEngine
from app.services.field_labeling.label_validator import LabelValidator
from app.services.field_labeling.label_mapper import LabelMapper
from app.services.field_labeling.labeling_orchestrator import LabelingOrchestrator
from app.services.field_labeling import FieldLabelingService

def test_confidence_engine_thresholding():
    classifications = [
        {"id": "cell_1", "label": "HEADER_BILL_NUMBER", "confidence": 0.99},
        {"id": "cell_2", "label": "HEADER_DUTY_SLIP", "confidence": 0.92},
        {"id": "cell_3", "label": "TOLL", "confidence": 0.96},
        {"id": "cell_4", "label": "PARKING", "confidence": 0.60},
    ]
    
    processed = ConfidenceEngine.process_classifications(classifications)
    
    assert processed[0]["label"] == "HEADER_BILL_NUMBER"
    assert processed[0]["confidence"] == 0.99
    
    # Coerced to UNKNOWN because 0.92 < 0.95
    assert processed[1]["label"] == "UNKNOWN"
    assert processed[1]["confidence"] == 0.92
    
    assert processed[2]["label"] == "TOLL"
    assert processed[2]["confidence"] == 0.96
    
    # Coerced to UNKNOWN because 0.60 < 0.95
    assert processed[3]["label"] == "UNKNOWN"
    assert processed[3]["confidence"] == 0.60

def test_label_validator():
    classifications = [
        {"id": "cell_1", "label": "HEADER_BILL_NUMBER", "confidence": 0.99},
        {"id": "cell_2", "label": "INVALID_LABEL_X", "confidence": 0.98},
        {"id": "cell_not_requested", "label": "TOLL", "confidence": 0.96},
    ]
    allowed_ids = {"cell_1", "cell_2"}
    
    validated = LabelValidator.validate_classifications(classifications, allowed_ids)
    
    assert len(validated) == 2
    assert validated[0]["id"] == "cell_1"
    assert validated[0]["label"] == "HEADER_BILL_NUMBER"
    
    # INVALID_LABEL_X is validated and coerced to UNKNOWN because it's not in the Enum
    assert validated[1]["id"] == "cell_2"
    assert validated[1]["label"] == "UNKNOWN"
    
    # cell_not_requested is skipped entirely because it's not in allowed_ids
    assert not any(v["id"] == "cell_not_requested" for v in validated)

def test_label_mapper():
    metadata = DocumentMetadata(file_name="test.docx")
    elements = [
        LabeledElement(id="cell_1", text="STB/2026/9001", coordinates={}, formatting={}, label="HEADER_BILL_NUMBER", confidence=0.99),
        LabeledElement(id="cell_2", text="DS-1002", coordinates={}, formatting={}, label="HEADER_DUTY_SLIP", confidence=0.98),
        LabeledElement(id="cell_3", text="Ashapura Travels", coordinates={}, formatting={}, label="HEADER_COMPANY", confidence=0.99),
        LabeledElement(id="cell_4", text="TS08EX6458", coordinates={}, formatting={}, label="VEHICLE_NUMBER", confidence=0.97),
        LabeledElement(id="cell_5", text="Sedan A/C", coordinates={}, formatting={}, label="VEHICLE_TYPE", confidence=0.96),
        LabeledElement(id="cell_6", text="130x15", coordinates={}, formatting={}, label="EXTRA_KM_FORMULA", confidence=0.99),
        LabeledElement(id="cell_7", text="150.00", coordinates={}, formatting={}, label="TOLL", confidence=0.99),
        LabeledElement(id="cell_8", text="50.00", coordinates={}, formatting={}, label="PARKING", confidence=0.99),
        LabeledElement(id="cell_9", text="4940.00", coordinates={}, formatting={}, label="TOTAL_AMOUNT", confidence=0.99),
    ]
    labeled_doc = LabeledDocument(metadata=metadata, elements=elements)
    
    mapped_dict = LabelMapper.to_extraction_dict(labeled_doc)
    
    assert mapped_dict["billNumber"] == "STB/2026/9001"
    assert mapped_dict["dutySlip"] == "DS-1002"
    assert mapped_dict["company"] == "Ashapura Travels"
    assert mapped_dict["vehicleNumber"] == "TS08EX6458"
    assert mapped_dict["vehicleType"] == "Sedan A/C"
    assert mapped_dict["extraKilometers"] == "130x15"
    assert mapped_dict["toll"] == "150.00"
    assert mapped_dict["parking"] == "50.00"
    assert mapped_dict["totalAmount"] == "4940.00"

def test_labeling_orchestrator_preparation_and_local_fallback():
    # Setup mock EnterpriseDocument
    metadata = DocumentMetadata(file_name="mock.docx")
    
    # Page 1
    # Paragraph outside table
    p1 = DocumentParagraph(
        id="p1",
        page_number=1,
        position=1,
        text="Portescap Invoice Details",
        paragraph_index=0,
        source_path="document/page/1/paragraph/0"
    )
    
    # Table 1 with rows and cells
    cell_ds_label = DocumentCell(
        id="c1", page_number=1, position=0, text="Duty Slip No", table_id="t1", row_index=0, column_index=0, rowspan=1, colspan=1, source_path="document/page/1/table/1/row/0/cell/0"
    )
    cell_ds_val = DocumentCell(
        id="c2", page_number=1, position=1, text="DS-9041", table_id="t1", row_index=0, column_index=1, rowspan=1, colspan=1, source_path="document/page/1/table/1/row/0/cell/1"
    )
    cell_veh_label = DocumentCell(
        id="c3", page_number=1, position=0, text="Vehicle No", table_id="t1", row_index=1, column_index=0, rowspan=1, colspan=1, source_path="document/page/1/table/1/row/1/cell/0"
    )
    cell_veh_val = DocumentCell(
        id="c4", page_number=1, position=1, text="TS08EX1234", table_id="t1", row_index=1, column_index=1, rowspan=1, colspan=1, source_path="document/page/1/table/1/row/1/cell/1"
    )
    
    row0 = DocumentRow(id="r0", page_number=1, position=0, row_index=0, cells=[cell_ds_label, cell_ds_val])
    row1 = DocumentRow(id="r1", page_number=1, position=1, row_index=1, cells=[cell_veh_label, cell_veh_val])
    
    table1 = DocumentTable(
        id="t1",
        page_number=1,
        position=2,
        table_number=1,
        number_of_rows=2,
        number_of_columns=2,
        rows=[row0, row1],
        source_path="document/page/1/table/1"
    )
    
    page1 = DocumentPage(
        id="page1",
        page_number=1,
        position=1,
        paragraphs=[p1],
        tables=[table1],
        reading_order=[
            {"order": 1, "type": "paragraph", "id": "p1", "text": "Portescap Invoice Details"},
            {"order": 2, "type": "table", "id": "t1", "table_number": 1}
        ]
    )
    
    doc = EnterpriseDocument(
        id="doc1",
        metadata=metadata,
        pages=[page1],
        paragraphs=[p1],
        tables=[table1],
        cells=[cell_ds_label, cell_ds_val, cell_veh_label, cell_veh_val],
        lines=[],
        runs=[]
    )
    
    # Reconstruct element contexts
    prepared = LabelingOrchestrator._prepare_elements(doc)
    
    assert len(prepared) == 5 # 1 paragraph + 4 cells
    
    # Check paragraph
    assert prepared[0]["id"] == "p1"
    assert prepared[0]["text"] == "Portescap Invoice Details"
    
    # Check cells and neighbor relationships
    # Cell 1 (Duty Slip No) - neighbor right should be DS-9041
    c1_prep = next(x for x in prepared if x["id"] == "c1")
    assert c1_prep["neighbors"]["right"] == "DS-9041"
    assert c1_prep["neighbors"]["below"] == "Vehicle No"
    
    # Cell 2 (DS-9041) - neighbor left is Duty Slip No
    c2_prep = next(x for x in prepared if x["id"] == "c2")
    assert c2_prep["neighbors"]["left"] == "Duty Slip No"
    assert c2_prep["neighbors"]["below"] == "TS08EX1234"
    
    # Run full service in local fallback mode
    labeled_doc = FieldLabelingService.label_document(doc)
    
    assert len(labeled_doc.elements) == 5
    
    # Portescap Invoice Details should be labeled HEADER_COMPANY
    p1_labeled = next(el for el in labeled_doc.elements if el.id == "p1")
    assert p1_labeled.label == "HEADER_COMPANY"
    
    # DS-9041 cell should be labeled HEADER_DUTY_SLIP
    c2_labeled = next(el for el in labeled_doc.elements if el.id == "c2")
    assert c2_labeled.label == "HEADER_DUTY_SLIP"
    assert c2_labeled.confidence >= 0.95
    
    # TS08EX1234 cell should be labeled VEHICLE_NUMBER
    c4_labeled = next(el for el in labeled_doc.elements if el.id == "c4")
    assert c4_labeled.label == "VEHICLE_NUMBER"
    assert c4_labeled.confidence >= 0.95
    
    # Convert labeled doc to standard extraction dict
    extracted = FieldLabelingService.map_to_parser_dict(labeled_doc)
    assert extracted["company"] == "Portescap Invoice Details"
    assert extracted["dutySlip"] == "DS-9041"
    assert extracted["vehicleNumber"] == "TS08EX1234"

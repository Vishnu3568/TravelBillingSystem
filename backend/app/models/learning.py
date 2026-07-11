from sqlalchemy import Column, Integer, String, Double, DateTime, Text
from datetime import datetime
from app.database import Base

class CorrectionHistory(Base):
    __tablename__ = "correction_history"

    id = Column(Integer, primary_key=True, index=True)
    original_value = Column(String(500), nullable=True)
    corrected_value = Column(String(500), nullable=True)
    field_type = Column(String(255), index=True, nullable=False)
    table_number = Column(Integer, nullable=True)
    row_index = Column(Integer, nullable=True)
    column_index = Column(Integer, nullable=True)
    company_name = Column(String(255), index=True, nullable=True)
    vehicle_number = Column(String(255), index=True, nullable=True)
    bill_number = Column(String(255), index=True, nullable=True)
    reviewer = Column(String(255), index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(String(500), nullable=True)
    ai_confidence = Column(Double, nullable=True)
    validation_status = Column(String(255), nullable=True)
    correction_count = Column(Integer, default=1, nullable=False)
    version = Column(Integer, default=1, nullable=False)

class CompanyPatterns(Base):
    __tablename__ = "company_patterns"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), unique=True, index=True, nullable=False)
    layout_name = Column(String(255), nullable=True)
    header_positions = Column(Text, nullable=True)  # JSON representation of header labels and cells
    field_locations = Column(Text, nullable=True)   # JSON representation of field coordinates
    preferred_labels = Column(Text, nullable=True)  # JSON list/dict of preferred label names
    frequently_corrected_fields = Column(Text, nullable=True) # JSON dictionary of field correction frequencies
    average_confidence = Column(Double, default=1.0, nullable=False)
    extraction_success_rate = Column(Double, default=1.0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class VehiclePatterns(Base):
    __tablename__ = "vehicle_patterns"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_type = Column(String(255), unique=True, index=True, nullable=False)
    layout_name = Column(String(255), nullable=True)
    recurring_structures = Column(Text, nullable=True) # JSON representation of table column layouts and formats
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class ReviewerStatistics(Base):
    __tablename__ = "reviewer_statistics"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_username = Column(String(255), unique=True, index=True, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    total_edits = Column(Integer, default=0, nullable=False)
    total_undos = Column(Integer, default=0, nullable=False)
    total_restores = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class ConfidenceHistory(Base):
    __tablename__ = "confidence_history"

    id = Column(Integer, primary_key=True, index=True)
    field_label = Column(String(255), unique=True, index=True, nullable=False)
    correct_predictions_count = Column(Integer, default=0, nullable=False)
    corrected_predictions_count = Column(Integer, default=0, nullable=False)
    adaptive_confidence = Column(Double, default=1.0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)  # JSON representation of global heuristics
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

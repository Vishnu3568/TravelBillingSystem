from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(String(255), primary_key=True, index=True) # e.g. "company:Portescap", "bill:123"
    entity_type = Column(String(255), index=True, nullable=False) # e.g. "Company", "Bill", "Vehicle"
    entity_id = Column(String(255), index=True, nullable=False) # original database primary key
    properties = Column(Text, nullable=True) # JSON representation of node details
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    outgoing_edges = relationship("GraphEdge", foreign_keys="[GraphEdge.source_node_id]", back_populates="source_node", cascade="all, delete-orphan")
    incoming_edges = relationship("GraphEdge", foreign_keys="[GraphEdge.target_node_id]", back_populates="target_node", cascade="all, delete-orphan")

class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(String(255), ForeignKey("graph_nodes.id"), nullable=False, index=True)
    target_node_id = Column(String(255), ForeignKey("graph_nodes.id"), nullable=False, index=True)
    relationship_type = Column(String(255), index=True, nullable=False) # e.g. "OWNS", "USES", "DRIVEN_BY"
    properties = Column(Text, nullable=True) # JSON representation of relationship attributes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Backreferences
    source_node = relationship("GraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("GraphNode", foreign_keys=[target_node_id], back_populates="incoming_edges")

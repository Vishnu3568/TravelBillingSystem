import json
import logging
from typing import Any
from sqlalchemy.orm import Session
from app.models.graph import GraphNode, GraphEdge
from app.models.bill import Bill
from app.services.knowledge_graph.entity_mapper import EntityMapper
from app.services.knowledge_graph.relationship_engine import RelationshipEngine

logger = logging.getLogger("graph_builder")

class GraphBuilder:
    @staticmethod
    def upsert_node(db: Session, node_id: str, entity_type: str, entity_id: str, properties: dict) -> GraphNode:
        """
        Inserts a node or updates its properties if it already exists.
        """
        node = db.query(GraphNode).filter(GraphNode.id == node_id).first()
        prop_str = json.dumps(properties)
        
        if not node:
            node = GraphNode(
                id=node_id,
                entity_type=entity_type,
                entity_id=str(entity_id),
                properties=prop_str
            )
            db.add(node)
        else:
            node.properties = prop_str
            node.updated_at = node.updated_at # triggers auto-update if configured, or python side update
            
        db.commit()
        db.refresh(node)
        return node

    @staticmethod
    def add_edge(db: Session, source_id: str, target_id: str, rel_type: str, properties: dict = None) -> GraphEdge:
        """
        Adds a directed edge between two nodes if it doesn't already exist.
        Ensures both endpoints exist first.
        """
        # Ensure source and target nodes exist in the database (create placeholders if missing)
        src_exists = db.query(GraphNode).filter(GraphNode.id == source_id).first()
        if not src_exists:
            # Create placeholder
            t_type = source_id.split(":")[0].capitalize()
            t_id = source_id.split(":")[1]
            GraphBuilder.upsert_node(db, source_id, t_type, t_id, {})

        tgt_exists = db.query(GraphNode).filter(GraphNode.id == target_id).first()
        if not tgt_exists:
            t_type = target_id.split(":")[0].capitalize()
            t_id = target_id.split(":")[1]
            GraphBuilder.upsert_node(db, target_id, t_type, t_id, {})

        # Check duplicate edge
        edge = db.query(GraphEdge).filter(
            GraphEdge.source_node_id == source_id,
            GraphEdge.target_node_id == target_id,
            GraphEdge.relationship_type == rel_type
        ).first()

        if not edge:
            edge = GraphEdge(
                source_node_id=source_id,
                target_node_id=target_id,
                relationship_type=rel_type,
                properties=json.dumps(properties or {})
            )
            db.add(edge)
            db.commit()
            db.refresh(edge)
        return edge

    @staticmethod
    def add_bill_node(db: Session, bill: Bill) -> None:
        """
        Incrementally adds/updates a Bill node and all its immediate relationships.
        """
        node_id, props = EntityMapper.map_entity("Bill", bill)
        GraphBuilder.upsert_node(db, node_id, "Bill", bill.id, props)

        # Upsert related Company node
        if bill.company_name:
            comp_id = EntityMapper.get_node_id("company", bill.company_name)
            GraphBuilder.upsert_node(db, comp_id, "Company", bill.company_name, {"name": bill.company_name})
            GraphBuilder.add_edge(db, comp_id, node_id, "OWNS")

        # Upsert related Vehicle node
        if bill.vehicle_name:
            veh_id = EntityMapper.get_node_id("vehicle", bill.vehicle_name)
            GraphBuilder.upsert_node(db, veh_id, "Vehicle", bill.vehicle_name, {"registration_number": bill.vehicle_name})
            GraphBuilder.add_edge(db, node_id, veh_id, "USES")

        # Upsert Driver node if parsed (using guest/driver bata representation)
        if bill.contact_person:
            driver_id = EntityMapper.get_node_id("driver", bill.contact_person)
            GraphBuilder.upsert_node(db, driver_id, "Driver", bill.contact_person, {"name": bill.contact_person})
            GraphBuilder.add_edge(db, node_id, driver_id, "DRIVEN_BY")

    @staticmethod
    def add_correction_node(db: Session, correction: Any) -> None:
        """
        Incrementally logs a reviewer correction node and connects it.
        """
        node_id, props = EntityMapper.map_entity("Correction", correction)
        GraphBuilder.upsert_node(db, node_id, "Correction", correction.id, props)

        # Link Reviewer -> Correction
        if correction.reviewer:
            rev_id = EntityMapper.get_node_id("reviewer", correction.reviewer)
            GraphBuilder.upsert_node(db, rev_id, "Reviewer", correction.reviewer, {"username": correction.reviewer})
            GraphBuilder.add_edge(db, rev_id, node_id, "CREATED_BY")

        # Link Correction -> Bill
        if correction.bill_number:
            # Query bill to find PK id
            bill = db.query(Bill).filter(Bill.bill_number == correction.bill_number).first()
            if bill:
                bill_node_id = EntityMapper.get_node_id("bill", bill.id)
                GraphBuilder.add_edge(db, node_id, bill_node_id, "MODIFIED")

    @staticmethod
    def add_validation_node(db: Session, bill_id: int, report: dict) -> None:
        """
        Logs a validation report node and connects it to the target Bill.
        """
        val_node_id = EntityMapper.get_node_id("validation_report", bill_id)
        props = {
            "overall_score": report.get("validation_summary", {}).get("overall_quality_score", 1.0),
            "issues_count": len(report.get("issues", []))
        }
        GraphBuilder.upsert_node(db, val_node_id, "ValidationReport", bill_id, props)

        # Link Bill -> ValidationReport
        bill_node_id = EntityMapper.get_node_id("bill", bill_id)
        GraphBuilder.add_edge(db, bill_node_id, val_node_id, "HAS")

    @staticmethod
    def add_conversation_node(db: Session, session_id: str, history: list, bill_id: int = None) -> None:
        """
        Logs a Copilot conversation session node and relates it to references.
        """
        conv_node_id = EntityMapper.get_node_id("conversation", session_id)
        props = {"session_id": session_id, "turns": len(history)}
        GraphBuilder.upsert_node(db, conv_node_id, "Conversation", session_id, props)

        # Link Conversation -> Bill reference
        if bill_id:
            bill_node_id = EntityMapper.get_node_id("bill", bill_id)
            GraphBuilder.add_edge(db, conv_node_id, bill_node_id, "REFERENCES")

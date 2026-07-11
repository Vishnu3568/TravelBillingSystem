import json
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.graph import GraphNode, GraphEdge
from app.models.bill import Bill
from app.models.learning import CorrectionHistory

class GraphSearch:
    @staticmethod
    def search_graph(db: Session, query: str) -> List[Dict[str, Any]]:
        """
        Executes query keywords matching to traverse connections and return list results.
        """
        q = query.lower().strip()
        results = []

        # Pattern 1: Find all companies connected to Crysta / vehicle type
        if "compan" in q and ("crysta" in q or "vehicle" in q or "sedan" in q):
            # Find Crysta vehicle nodes
            target_veh = "crysta" if "crysta" in q else "sedan" if "sedan" in q else ""
            vehicles = db.query(GraphNode).filter(
                GraphNode.entity_type == "Vehicle",
                GraphNode.id.like(f"%{target_veh}%")
            ).all()
            
            connected_companies = set()
            for v in vehicles:
                # Find bills using this vehicle
                edges_uses = db.query(GraphEdge).filter(
                    GraphEdge.target_node_id == v.id,
                    GraphEdge.relationship_type == "USES"
                ).all()
                
                for edge in edges_uses:
                    # Find company owning this bill
                    edges_owns = db.query(GraphEdge).filter(
                        GraphEdge.target_node_id == edge.source_node_id,
                        GraphEdge.relationship_type == "OWNS"
                    ).all()
                    for edge_owns in edges_owns:
                        # Extract company name
                        comp_name = edge_owns.source_node_id.split(":")[1]
                        connected_companies.add(comp_name)
                        
            for comp in connected_companies:
                results.append({
                    "entity": f"company:{comp}",
                    "type": "Company",
                    "description": f"Connected to vehicle type through historical invoices"
                })

        # Pattern 2: Find all reviewers that corrected Portescap invoices
        elif "reviewer" in q and "portescap" in q:
            # Get Portescap bills
            bills = db.query(Bill).filter(Bill.company_name.like("%Portescap%")).all()
            bill_numbers = [b.bill_number for b in bills]
            
            if bill_numbers:
                reviewers = db.query(CorrectionHistory.reviewer).filter(
                    CorrectionHistory.bill_number.in_(bill_numbers)
                ).distinct().all()
                for (rev,) in reviewers:
                    if rev:
                        results.append({
                            "entity": f"reviewer:{rev}",
                            "type": "Reviewer",
                            "description": f"Corrected Portescap bills"
                        })

        # Pattern 3: Find bills sharing the same vehicle
        elif "bills" in q and "same vehicle" in q:
            # Group bills by vehicle registration
            veh_groups = db.query(
                Bill.vehicle_name,
                func.count(Bill.id)
            ).group_by(Bill.vehicle_name).having(func.count(Bill.id) > 1).all()
            
            for veh, count in veh_groups:
                if veh:
                    results.append({
                        "entity": f"vehicle:{veh}",
                        "type": "Vehicle",
                        "description": f"Shared by {count} distinct invoices"
                    })

        # Pattern 4: Validation issues related to Driver Bata
        elif "validation" in q and ("driver" in q or "bata" in q):
            # Query corrections matching bata fields
            corrections = db.query(CorrectionHistory).filter(
                CorrectionHistory.field_type == "driverBata"
            ).limit(10).all()
            for c in corrections:
                results.append({
                    "entity": f"correction:{c.id}",
                    "type": "Correction",
                    "description": f"Driver Bata corrected in Bill {c.bill_number} (AI: '{c.original_value}' -> Rev: '{c.corrected_value}')"
                })

        # Default fallback: Keyword lookup in node properties
        if not results:
            # Find any node containing keyword in its ID
            keywords = q.split()
            if keywords:
                nodes = db.query(GraphNode).filter(
                    GraphNode.id.like(f"%{keywords[0]}%")
                ).limit(10).all()
                for n in nodes:
                    results.append({
                        "entity": n.id,
                        "type": n.entity_type,
                        "description": f"Node found matching search keyword"
                    })

        return results

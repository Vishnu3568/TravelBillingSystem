from __future__ import annotations

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings
from app.models.bill import Bill
from app.models.learning import CorrectionHistory
from app.models.graph import GraphNode, GraphEdge

# Import Graph Service modules
from app.services.knowledge_graph.entity_mapper import EntityMapper
from app.services.knowledge_graph.relationship_engine import RelationshipEngine
from app.services.knowledge_graph.graph_builder import GraphBuilder
from app.services.knowledge_graph.graph_queries import GraphQueries
from app.services.knowledge_graph.graph_search import GraphSearch
from app.services.knowledge_graph.graph_statistics import GraphStatistics
from app.services.knowledge_graph.graph_export import GraphExport
from app.services.knowledge_graph.graph_visualizer import GraphVisualizer
from app.services.knowledge_graph.graph_service import GraphService

# Setup DB session fixture
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

def test_entity_mapper_and_ids():
    node_id = EntityMapper.get_node_id("company", "Portescap Co")
    assert node_id == "company:Portescap_Co"

def test_relationship_extraction():
    class DummyBill:
        id = 123
        company_name = "Portescap"
        vehicle_name = "TS09EX6458"
        created_by = "owner2"
        
    rels = RelationshipEngine.extract_bill_relationships(DummyBill())
    assert len(rels) == 3
    assert rels[0] == ("company:Portescap", "bill:123", "OWNS", {})

def test_graph_builder_and_queries(db_session):
    # Upsert source node
    GraphBuilder.upsert_node(db_session, "company:Microsoft", "Company", "Microsoft", {"name": "Microsoft"})
    # Upsert target node
    GraphBuilder.upsert_node(db_session, "bill:50", "Bill", "50", {"grand_total": 3500.0})
    
    # Add Edge
    GraphBuilder.add_edge(db_session, "company:Microsoft", "bill:50", "OWNS")
    
    # Trace Neighbors
    neighbors = GraphQueries.get_connected_nodes(db_session, "company:Microsoft")
    assert len(neighbors) == 1
    assert neighbors[0].id == "bill:50"
    
    # Get Subgraph
    subgraph = GraphQueries.get_subgraph(db_session, "company:Microsoft", depth=1)
    assert len(subgraph.nodes) == 2
    assert len(subgraph.edges) == 1

def test_incremental_updates(db_session):
    bill = Bill(
        id=99,
        bill_number="BILL-99",
        company_name="Microsoft",
        vehicle_name="Crysta",
        duty_slip_no="DS-99",
        grand_total=1000.0,
        created_by="owner2"
    )
    db_session.add(bill)
    db_session.commit()
    
    # Save triggers node creation
    GraphBuilder.add_bill_node(db_session, bill)
    
    # Check nodes
    n_bill = db_session.query(GraphNode).filter(GraphNode.id == "bill:99").first()
    assert n_bill is not None
    
    n_comp = db_session.query(GraphNode).filter(GraphNode.id == "company:Microsoft").first()
    assert n_comp is not None

def test_graph_search(db_session):
    # Seed nodes
    GraphBuilder.upsert_node(db_session, "company:Microsoft", "Company", "Microsoft", {})
    GraphBuilder.upsert_node(db_session, "bill:10", "Bill", "10", {})
    GraphBuilder.upsert_node(db_session, "vehicle:Crysta", "Vehicle", "Crysta", {})
    
    # Connect them
    GraphBuilder.add_edge(db_session, "company:Microsoft", "bill:10", "OWNS")
    GraphBuilder.add_edge(db_session, "bill:10", "vehicle:Crysta", "USES")
    
    # Find all companies connected to Crysta
    results = GraphSearch.search_graph(db_session, "Find all companies connected to Crysta")
    assert len(results) == 1
    assert results[0]["entity"] == "company:Microsoft"

def test_graph_statistics(db_session):
    GraphBuilder.upsert_node(db_session, "company:Microsoft", "Company", "Microsoft", {})
    stats = GraphStatistics.get_statistics(db_session)
    assert stats.total_nodes == 1
    assert stats.relationship_density == 0.0

def test_graph_export(db_session):
    GraphBuilder.upsert_node(db_session, "company:Microsoft", "Company", "Microsoft", {})
    
    json_data = GraphExport.export_as_json(db_session)
    assert "nodes" in json_data
    
    csv_data = GraphExport.export_as_csv(db_session)
    assert "# NODES" in csv_data
    
    xml_data = GraphExport.export_as_graphml(db_session)
    assert "<graphml" in xml_data
    
    cypher_script = GraphExport.export_as_cypher(db_session)
    assert "CREATE" in cypher_script

def test_feature_flags_and_facade(db_session):
    # Disable flag
    settings.USE_ENTERPRISE_GRAPH = False
    
    bill = Bill(
        id=99,
        bill_number="BILL-99",
        company_name="Microsoft",
        vehicle_name="Crysta",
        duty_slip_no="DS-99",
        grand_total=1000.0,
        created_by="owner2"
    )
    # register save should bypass if flag is false
    GraphService.register_bill_save(db_session, bill)
    
    # Check no nodes in graph
    cnt = db_session.query(GraphNode).count()
    assert cnt == 0
    
    # Enable flag
    settings.USE_ENTERPRISE_GRAPH = True
    GraphService.register_bill_save(db_session, bill)
    assert db_session.query(GraphNode).count() > 0

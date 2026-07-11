from fastapi import APIRouter, Depends, Response, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user, RoleChecker
from app.services.knowledge_graph.graph_service import GraphService
from app.services.knowledge_graph.graph_queries import GraphQueries
from app.models.graph import GraphNode
import json

router = APIRouter(prefix="/api/graph", tags=["graph"])

auth_guard = get_current_user
owner_guard = RoleChecker(["OWNER"])

@router.get("/statistics")
def get_graph_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    Returns calculated connectivity metrics, total nodes, and edge counts.
    """
    return GraphService.get_analytics(db)

@router.get("/search")
def search_graph(
    query: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    Executes a connection search for crystallizing patterns or reviewers.
    """
    return GraphService.search(db, query)

@router.get("/entity/{node_id}")
def get_entity_node(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    Retrieves properties and fields for a specific Graph Node.
    """
    node = db.query(GraphNode).filter(GraphNode.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found in the Knowledge Graph."
        )
    try:
        props = json.loads(node.properties or "{}")
    except Exception:
        props = {}
    return {
        "id": node.id,
        "entity_type": node.entity_type,
        "entity_id": node.entity_id,
        "properties": props
    }

@router.get("/relationships/{node_id}")
def get_node_relationships(
    node_id: str,
    depth: int = Query(1, ge=1, le=3),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    Retrieves immediate subgraphs and edges traversing from node_id.
    """
    subgraph = GraphQueries.get_subgraph(db, node_id, depth)
    return subgraph.model_dump()

@router.get("/export")
def export_graph_store(
    format: str = Query("json", pattern="^(json|csv|graphml|cypher)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    """
    Exports the Enterprise Knowledge Graph.
    Guarded for OWNER access only.
    """
    exported_data = GraphService.export_graph(db, format)
    
    media_type = "application/json"
    filename = f"knowledge_graph_export.{format}"
    
    if format == "csv":
        media_type = "text/csv"
    elif format == "graphml":
        media_type = "application/xml"
    elif format == "cypher":
        media_type = "text/plain"
        
    return Response(
        content=exported_data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

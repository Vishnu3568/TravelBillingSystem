import json
import csv
import io
from sqlalchemy.orm import Session
from app.models.graph import GraphNode, GraphEdge
from app.services.knowledge_graph.graph_visualizer import GraphVisualizer

class GraphExport:
    @staticmethod
    def export_as_json(db: Session) -> str:
        """
        Exports the entire graph as a JSON string representation.
        """
        data = GraphVisualizer.generate_visualization_data(db)
        return json.dumps(data, indent=2)

    @staticmethod
    def export_as_csv(db: Session) -> str:
        """
        Exports the graph nodes and edges as CSV strings combined in a text block.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Nodes Section
        writer.writerow(["# NODES"])
        writer.writerow(["ID", "Type", "Properties"])
        nodes = db.query(GraphNode).all()
        for n in nodes:
            writer.writerow([n.id, n.entity_type, n.properties or "{}"])
            
        writer.writerow([])
        
        # Edges Section
        writer.writerow(["# EDGES"])
        writer.writerow(["Source", "Target", "Type"])
        edges = db.query(GraphEdge).all()
        for e in edges:
            writer.writerow([e.source_node_id, e.target_node_id, e.relationship_type])
            
        return output.getvalue()

    @staticmethod
    def export_as_graphml(db: Session) -> str:
        """
        Exports the graph nodes and edges as a standard GraphML XML string.
        """
        nodes = db.query(GraphNode).all()
        edges = db.query(GraphEdge).all()

        xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns" ',
            '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ',
            '         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns ',
            '         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">',
            '  <graph id="G" edgedefault="directed">'
        ]

        # Add keys for attributes
        xml.append('    <key id="d0" for="node" attr.name="entity_type" attr.type="string"/>')
        xml.append('    <key id="d1" for="node" attr.name="properties" attr.type="string"/>')

        # Add nodes
        for n in nodes:
            xml.append(f'    <node id="{n.id}">')
            xml.append(f'      <data key="d0">{n.entity_type}</data>')
            escaped_props = (n.properties or "{}").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            xml.append(f'      <data key="d1">{escaped_props}</data>')
            xml.append('    </node>')

        # Add edges
        for idx, e in enumerate(edges):
            xml.append(f'    <edge id="e{idx}" source="{e.source_node_id}" target="{e.target_node_id}">')
            xml.append(f'      <data key="label">{e.relationship_type}</data>')
            xml.append('    </edge>')

        xml.append('  </graph>')
        xml.append('</graphml>')
        return "\n".join(xml)

    @staticmethod
    def export_as_cypher(db: Session) -> str:
        """
        Generates copyable Neo4j Cypher scripts to instantiate nodes and relationships.
        """
        nodes = db.query(GraphNode).all()
        edges = db.query(GraphEdge).all()

        cypher = ["// Neo4j Cypher Export Query"]
        
        # Create Nodes
        for n in nodes:
            # Clean node ID to act as variable name
            var_name = n.id.replace(":", "_").replace("-", "_")
            label = n.entity_type
            try:
                props_dict = json.loads(n.properties or "{}")
            except Exception:
                props_dict = {}
                
            # Normalize properties mapping keys
            props_list = [f"{k}: '{v}'" for k, v in props_dict.items() if isinstance(v, (str, int, float))]
            props_str = f" {{ {', '.join(props_list)} }}" if props_list else ""
            
            cypher.append(f"CREATE ({var_name}:{label}{props_str})")
            
        cypher.append("\n// Create Relationships")
        # Create Edges
        for e in edges:
            src_var = e.source_node_id.replace(":", "_").replace("-", "_")
            tgt_var = e.target_node_id.replace(":", "_").replace("-", "_")
            rel = e.relationship_type
            cypher.append(f"CREATE ({src_var})-[:{rel}]->({tgt_var})")
            
        return "\n".join(cypher)

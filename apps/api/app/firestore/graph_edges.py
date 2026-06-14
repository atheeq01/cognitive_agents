import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class GraphEdgesStore:
    def __init__(self):
        self.mock_mode = False
        try:
            from firebase_admin import firestore
            self.db = firestore.client()
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore for GraphEdgesStore. Running in mock mode: {e}")
            self.mock_mode = True

    def save_edges(self, project_id: str, ucd_id: str, edges: List[Dict[str, Any]]):
        """
        Saves knowledge graph temporal edges to Firestore.
        Path: projects/{project_id}/graph_edges/{edge_id}
        """
        if self.mock_mode:
            logger.info(f"[MOCK FIRESTORE] Saved {len(edges)} temporal edges to project {project_id}")
            return
            
        try:
            batch = self.db.batch()
            collection_ref = self.db.collection("projects").document(str(project_id)).collection("graph_edges")
            
            for edge in edges:
                edge_id = str(uuid.uuid4())
                doc_ref = collection_ref.document(edge_id)
                payload = {
                    "edge_id": edge_id,
                    "source_doc_id": str(ucd_id),
                    "source_entity_id": edge.get("source_entity_id"),
                    "target_entity_id": edge.get("target_entity_id"),
                    "relationship": edge.get("relationship"),
                    "score": edge.get("score", 0.0),
                    "valid_from": edge.get("valid_from"),
                    "valid_to": edge.get("valid_to"),
                    "created_at": datetime.utcnow()
                }
                batch.set(doc_ref, payload)
                
            batch.commit()
            logger.info(f"Successfully wrote {len(edges)} graph edges for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to write graph edges to Firestore: {e}")
            raise

graph_edges_store = GraphEdgesStore()

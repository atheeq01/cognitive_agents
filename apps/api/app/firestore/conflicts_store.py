import logging
import uuid
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ConflictsStore:
    def __init__(self):
        self.mock_mode = False
        try:
            from firebase_admin import firestore
            self.db = firestore.client()
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore for ConflictsStore. Running in mock mode: {e}")
            self.mock_mode = True

    def route_to_human_review(self, project_id: str, conflict_data: Dict[str, Any]) -> str:
        """
        Routes a confirmed disagreement to the Firestore Human Review Queue.
        Path: projects/{project_id}/conflicts/{conflict_id}
        """
        conflict_id = str(uuid.uuid4())
        
        payload = {
            "conflict_id": conflict_id,
            "project_id": str(project_id),
            "status": "pending_review", # Human review required
            "severity": conflict_data.get("severity", "LOW"),
            "conflict_type": conflict_data.get("conflict_type", "factual"),
            "evidence_a": conflict_data.get("evidence_a"),
            "evidence_b": conflict_data.get("evidence_b"),
            "modality_a": conflict_data.get("modality_a"),
            "modality_b": conflict_data.get("modality_b"),
            "created_at": datetime.utcnow()
        }
        
        if self.mock_mode:
            logger.info(f"[MOCK FIRESTORE] Wrote conflict {conflict_id} to project {project_id}")
            return conflict_id
            
        try:
            doc_ref = self.db.collection("projects").document(str(project_id)).collection("conflicts").document(conflict_id)
            doc_ref.set(payload)
            logger.info(f"Successfully routed conflict {conflict_id} to human review queue for project {project_id}")
            return conflict_id
        except Exception as e:
            logger.error(f"Failed to write conflict to Firestore: {e}")
            raise

conflicts_store = ConflictsStore()

import os
import logging
import firebase_admin
from firebase_admin import firestore
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FirestoreService:
    def __init__(self):
        # Make sure the emulator host is applied before initializing the client.
        # main.py sets this, but guard here too in case of import ordering issues.
        emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
        if emulator_host:
            logger.info(f"[FirestoreService] Using emulator at {emulator_host}")
        else:
            logger.warning(
                "[FirestoreService] FIRESTORE_EMULATOR_HOST is NOT set — "
                "connecting to real Firestore (this will fail in local dev!)"
            )

        if not firebase_admin._apps:
            project_id = os.environ.get("FIREBASE_PROJECT_ID", "omnimind-499716")
            logger.info(f"[FirestoreService] Initializing Firebase app | project={project_id}")
            firebase_admin.initialize_app(options={"projectId": project_id})

        self.db = firestore.client()
        logger.info("[FirestoreService] Firestore client initialized successfully")

    async def update_job_status(
        self,
        project_id: str,
        document_id: str,
        stage_name: str,
        progress: int,
        status: str = "processing",
        document_name: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
    ):
        """
        Updates the job status document in Firestore.
        Path: projects/{project_id}/jobs/{document_id}
        """
        import asyncio
        try:
            doc_ref = (
                self.db.collection("projects")
                .document(project_id)
                .collection("jobs")
                .document(document_id)
            )

            data: Dict[str, Any] = {
                "id": document_id,
                "projectId": project_id,
                "status": status,
                "stage_name": stage_name,
                "progress": progress,
            }

            if document_name:
                data["documentName"] = document_name
            if results:
                data["results"] = results

            await asyncio.to_thread(doc_ref.set, data, merge=True)
            logger.info(
                f"[FirestoreService] Job status updated | "
                f"project={project_id} | document={document_id} | "
                f"stage={stage_name!r} | progress={progress}% | status={status}"
            )

        except Exception as e:
            logger.error(
                f"[FirestoreService] Failed to update job status | "
                f"project={project_id} | document={document_id} | error={e}"
            )

    async def get_completed_documents(self, project_id: str) -> list[dict]:
        """
        Retrieves all completed document jobs for the given project.
        """
        from google.cloud.firestore_v1.base_query import FieldFilter
        import asyncio
        try:
            query = (
                self.db.collection("projects")
                .document(project_id)
                .collection("jobs")
                .where(filter=FieldFilter("status", "==", "completed"))
            )
            def _stream():
                return list(query.stream())
            docs = await asyncio.to_thread(_stream)
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"[FirestoreService] Failed to get completed documents: {e}")
            return []

    async def update_project_report(self, project_id: str, report: dict):
        """
        Writes the synthesized intelligence report to the project document.
        """
        try:
            from datetime import datetime, timezone
            import asyncio
            doc_ref = self.db.collection("projects").document(project_id)
            
            data = {
                "project_report": report,
                "last_synthesized_at": datetime.now(timezone.utc).isoformat()
            }
            
            await asyncio.to_thread(doc_ref.set, data, merge=True)
            logger.info(f"[FirestoreService] Project report updated | project={project_id}")
        except Exception as e:
            logger.error(f"[FirestoreService] Failed to update project report: {e}")


firestore_service = FirestoreService()

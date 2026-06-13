import json
from google.cloud import pubsub_v1
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class PubSubService:
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.project_id = settings.FIREBASE_PROJECT_ID or "demo-omnimind"
        self.topic_path = self.publisher.topic_path(self.project_id, "document-uploads")

    async def publish_document_approved(self, project_id: str, document_id: str, gcs_path: str):
        payload = {
            "project_id": str(project_id),
            "document_id": str(document_id),
            "gcs_path": gcs_path,
            "action": "process"
        }
        
        data = json.dumps(payload).encode("utf-8")
        future = self.publisher.publish(self.topic_path, data)
        future.result()

pubsub_service = PubSubService()

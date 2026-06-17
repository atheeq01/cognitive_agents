import asyncio
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
        self.member_topic_path = self.publisher.topic_path(self.project_id, "member-events")

    async def publish_document_approved(self, project_id: str, document_id: str, gcs_path: str):
        payload = {
            "project_id": str(project_id),
            "document_id": str(document_id),
            "gcs_path": gcs_path,
            "action": "process"
        }
        
        data = json.dumps(payload).encode("utf-8")
        loop = asyncio.get_event_loop()
        try:
            future = self.publisher.publish(self.topic_path, data)
            await loop.run_in_executor(None, future.result)
        except Exception as e:
            logger.error(f"Failed to publish Pub/Sub message: {e}")
            raise

    async def _publish_member_event(self, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        loop = asyncio.get_event_loop()
        try:
            future = self.publisher.publish(self.member_topic_path, data)
            await loop.run_in_executor(None, future.result)
        except Exception as e:
            logger.error(f"Failed to publish member event to Pub/Sub: {e}")

    async def publish_member_invited(self, project_id: str, email: str, role: str):
        await self._publish_member_event({
            "action": "member_invited",
            "project_id": str(project_id),
            "email": email,
            "role": role
        })

    async def publish_member_accepted(self, project_id: str, user_id: str):
        await self._publish_member_event({
            "action": "member_accepted",
            "project_id": str(project_id),
            "user_id": str(user_id)
        })

    async def publish_role_changed(self, project_id: str, user_id: str, new_role: str):
        await self._publish_member_event({
            "action": "role_changed",
            "project_id": str(project_id),
            "user_id": str(user_id),
            "new_role": new_role
        })

pubsub_service = PubSubService()

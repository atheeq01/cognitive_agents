import asyncio
import json
from google.cloud import pubsub_v1
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

class PubSubService:
    def __init__(self):
        try:
            self.publisher = pubsub_v1.PublisherClient()
        except Exception as e:
            logger.error(f"Failed to initialize PubSub publisher: {e}")
            self.publisher = None
        self.project_id = settings.FIREBASE_PROJECT_ID or "demo-omnimind"
        if self.publisher:
            self.topic_path = self.publisher.topic_path(self.project_id, "document-uploads")
            self.member_topic_path = self.publisher.topic_path(self.project_id, "member-events")

    async def publish_document_approved(self, project_id: str, document_id: str, gcs_path: str):
        payload = {
            "project_id": str(project_id),
            "document_id": str(document_id),
            "gcs_path": gcs_path,
            "action": "process"
        }
        
        if settings.ENVIRONMENT == "local":
            import urllib.request
            import base64
            
            pubsub_message = {
                "message": {
                    "data": base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8"),
                    "messageId": "mock-local-id"
                }
            }
            
            def _send():
                try:
                    req = urllib.request.Request(
                        "http://localhost:8001/ingest/",
                        data=json.dumps(pubsub_message).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    # Increase timeout to 300 seconds to allow the worker's synchronous pipeline to finish
                    urllib.request.urlopen(req, timeout=300)
                    logger.info(f"[LOCAL DEV] Directly pushed event to local worker at :8001 for {document_id}")
                except Exception as e:
                    logger.error(f"[LOCAL DEV] Failed to push to local worker (is it running on port 8001?): {e}")
            
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, _send)
            return
            
        if not self.publisher:
            logger.warning(f"No pubsub publisher available, dropping message: {payload}")
            return
            
        data = json.dumps(payload).encode("utf-8")
        loop = asyncio.get_running_loop()
        try:
            future = self.publisher.publish(self.topic_path, data)
            await loop.run_in_executor(None, future.result)
        except Exception as e:
            logger.error(f"Failed to publish Pub/Sub message: {e}")
            raise

    async def _publish_member_event(self, payload: dict):
        if not self.publisher:
            logger.warning(f"No pubsub publisher available, dropping message: {payload}")
            return
            
        data = json.dumps(payload).encode("utf-8")
        loop = asyncio.get_running_loop()
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

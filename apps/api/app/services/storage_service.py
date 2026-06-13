from google.cloud import storage
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = settings.GCS_BUCKET_NAME

    async def upload_document(self, project_id: str, document_id: str, filename: str, content: bytes) -> str:
        gcs_path = f"projects/{project_id}/documents/{document_id}/{filename}"
        
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(content)
        return gcs_path

storage_service = StorageService()

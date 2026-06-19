import asyncio
from google.cloud import storage
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = settings.GCS_BUCKET_NAME

    async def upload_document(self, project_id: str, document_id: str, filename: str, file_obj) -> str:
        gcs_path = f"projects/{project_id}/documents/{document_id}/{filename}"
        
        loop = asyncio.get_running_loop()
        def _upload():
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            blob.upload_from_file(file_obj)
        
        await loop.run_in_executor(None, _upload)
        return gcs_path

    async def delete_document(self, gcs_path: str) -> None:
        loop = asyncio.get_running_loop()
        def _delete():
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            blob.delete()
        
        await loop.run_in_executor(None, _delete)
        logger.info(f"[StorageService] Deleted blob | path={gcs_path}")

storage_service = StorageService()

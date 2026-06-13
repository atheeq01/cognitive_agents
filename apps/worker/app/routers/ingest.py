from fastapi import APIRouter, Request, HTTPException, status
import logging
import base64
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/")
async def handle_pubsub_push(request: Request):
    """
    Endpoint for Google Cloud Pub/Sub Push Subscriptions.
    Receives events when a document is approved and ready for processing.
    """
    envelope = await request.json()
    if not envelope:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request")
        
    message = envelope.get("message")
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request: missing message")
        
    try:
        # Decode the payload
        data = base64.b64decode(message["data"]).decode("utf-8")
        payload = json.loads(data)
        
        project_id = payload.get("project_id")
        document_id = payload.get("document_id")
        gcs_path = payload.get("gcs_path")
        
        logger.info(f"Worker received processing job for document {document_id} in project {project_id}")
        
        # Trigger the UCD Builder normalization process
        logger.info(f"Processing {gcs_path}...")
        
        return {"status": "processing"}
        
    except Exception as e:
        logger.error(f"Error processing pubsub message: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

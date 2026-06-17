from fastapi import APIRouter, Request, HTTPException, status
import logging
import base64
import json
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

# Lazy import processors to avoid crashing if optional dependencies are missing at startup
def _get_processors():
    from app.processors.document_ai_processor import document_ai_processor
    from app.processors.speech_to_text import speech_to_text_processor
    from app.processors.vision_ocr import vision_ocr_processor
    from app.ucd.section_chunker import section_chunker
    return document_ai_processor, speech_to_text_processor, vision_ocr_processor, section_chunker


async def _process_document(project_id: str, document_id: str, gcs_path: str):
    """
    Core processing pipeline:
    1. Download the file from GCS
    2. Route to the correct processor based on MIME type
    3. Chunk the extracted text using the UCD section chunker
    """
    try:
        # Step 1: Download file bytes from GCS
        from google.cloud import storage as gcs
        loop = asyncio.get_event_loop()

        def _download():
            client = gcs.Client()
            bucket_name = gcs_path.split("/")[0] if "/" not in gcs_path else None
            blob = client.blob(gcs_path) if bucket_name else client.bucket(
                "omnimind-documents"
            ).blob(gcs_path)
            return blob.download_as_bytes()

        try:
            file_bytes = await loop.run_in_executor(None, _download)
        except Exception as e:
            logger.warning(f"Could not download from GCS (may be emulated): {e}")
            file_bytes = b""  # Fall through to mock processors

        # Step 2: Determine MIME type and route to the correct processor
        doc_ai, speech_processor, vision_processor, chunker = _get_processors()

        import magic
        mime_type = magic.from_buffer(file_bytes, mime=True) if file_bytes else "application/pdf"

        if mime_type in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            result = await vision_processor.process_image(file_bytes, mime_type)
        elif mime_type in ("audio/mpeg", "audio/wav", "audio/ogg", "audio/flac"):
            result = await speech_processor.process_audio(file_bytes, mime_type)
        else:
            # Default: treat as a document (PDF, text, DOCX, etc.)
            result = await doc_ai.process_document(file_bytes, mime_type)

        raw_text = result.get("raw_text", "")
        modality = result.get("modality", "unknown")

        # Step 3: Chunk the extracted text
        chunks = chunker.chunk_document(raw_text) if raw_text else []

        logger.info(
            f"[Worker] Processed document {document_id} "
            f"(modality={modality}, chunks={len(chunks)}) in project {project_id}"
        )

        # TODO: embed chunks and upsert into Pinecone vector store
        # TODO: write job status update to Firestore

    except Exception as e:
        logger.error(f"[Worker] Pipeline failed for document {document_id}: {e}", exc_info=True)
        raise


@router.post("/")
async def handle_pubsub_push(request: Request):
    """
    Endpoint for Google Cloud Pub/Sub Push Subscriptions.
    Receives events when a document is approved and ready for processing.
    Returns 200 immediately so Pub/Sub acks the message;
    actual processing runs as a background task.
    """
    envelope = await request.json()
    if not envelope:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request: empty body")
        
    message = envelope.get("message")
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request: missing message")
        
    try:
        data = base64.b64decode(message["data"]).decode("utf-8")
        payload = json.loads(data)
        
        project_id = payload.get("project_id")
        document_id = payload.get("document_id")
        gcs_path = payload.get("gcs_path")

        if not all([project_id, document_id, gcs_path]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payload missing required fields: project_id, document_id, gcs_path"
            )
        
        logger.info(f"[Worker] Received job for document {document_id} in project {project_id}")

        asyncio.create_task(_process_document(project_id, document_id, gcs_path))
        
        return {"status": "accepted", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Worker] Error decoding Pub/Sub message: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Malformed message: {e}")

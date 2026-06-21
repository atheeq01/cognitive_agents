import uuid
import magic
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.document import Document, DocumentStatus
from app.models.project import Project
from app.services.storage_service import storage_service
from app.services.pubsub_service import pubsub_service

MAX_FILE_SIZE = 50 * 1024 * 1024 # 50 MB
ALLOWED_MIME_TYPES = [
    "application/pdf", 
    "text/plain", 
    "audio/mpeg", 
    "image/jpeg", 
    "image/png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "application/zip" # Fallback for python-magic detecting office docs as zip
]

class DocumentService:
    @staticmethod
    async def list_documents(db: AsyncSession, project_id: uuid.UUID, status_filter: Optional[str] = None) -> list[Document]:
        query = select(Document).where(Document.project_id == project_id)
        if status_filter:
            try:
                status_enum = DocumentStatus(status_filter)
                query = query.where(Document.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def upload_document(db: AsyncSession, project_id: uuid.UUID, file: UploadFile, user_id: uuid.UUID) -> Document:
        # Read small chunk to check magic
        header_chunk = await file.read(2048)
        await file.seek(0)
        
        size_bytes = file.size
        if size_bytes is not None and size_bytes > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 50MB limit")
            
        mime_type = magic.from_buffer(header_chunk, mime=True)
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported file type: {mime_type}")
            
        project = await db.execute(select(Project).where(Project.project_id == project_id))
        project_obj = project.scalars().first()
        if not project_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
            
        doc_status = DocumentStatus.APPROVED
        
        document_id = uuid.uuid4()
        gcs_path = await storage_service.upload_document(str(project_id), str(document_id), file.filename, file.file)
        
        document = Document(
            document_id=document_id,
            project_id=project_id,
            uploader_id=user_id,
            filename=file.filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            gcs_path=gcs_path,
            status=doc_status
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        if doc_status == DocumentStatus.APPROVED:
            await pubsub_service.publish_document_approved(str(project_id), str(document_id), gcs_path)
            
        return document

    @staticmethod
    async def approve_document(db: AsyncSession, project_id: uuid.UUID, document_id: uuid.UUID) -> Document:
        result = await db.execute(select(Document).where(
            Document.project_id == project_id,
            Document.document_id == document_id
        ))
        document = result.scalars().first()
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            
        if document.status != DocumentStatus.PENDING_APPROVAL:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document is not pending approval")
            
        document.status = DocumentStatus.APPROVED
        await db.commit()
        await db.refresh(document)
        
        await pubsub_service.publish_document_approved(str(project_id), str(document_id), document.gcs_path)
        return document

    @staticmethod
    async def delete_document(db: AsyncSession, project_id: uuid.UUID, document_id: uuid.UUID) -> None:
        import logging
        logger = logging.getLogger(__name__)

        result = await db.execute(select(Document).where(
            Document.project_id == project_id,
            Document.document_id == document_id
        ))
        document = result.scalars().first()
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        gcs_path = document.gcs_path

        # 1. Delete from PostgreSQL
        await db.delete(document)
        await db.commit()

        # 2. Delete the Firestore job record so Intelligence tab updates
        try:
            import firebase_admin
            from firebase_admin import firestore as fb_firestore
            import os

            if not firebase_admin._apps:
                project = os.environ.get("FIREBASE_PROJECT_ID", "omnimind-499716")
                firebase_admin.initialize_app(options={"projectId": project})

            fs_client = fb_firestore.client()
            job_ref = (
                fs_client.collection("projects")
                .document(str(project_id))
                .collection("jobs")
                .document(str(document_id))
            )
            job_ref.delete()
            logger.info(f"[DocumentService] Deleted Firestore job | project={project_id} | document={document_id}")
        except Exception as e:
            logger.warning(f"[DocumentService] Failed to delete Firestore job (non-fatal): {e}")

        # 3. Delete the file from GCS
        try:
            if gcs_path:
                await storage_service.delete_document(gcs_path)
                logger.info(f"[DocumentService] Deleted GCS file | path={gcs_path}")
        except Exception as e:
            logger.warning(f"[DocumentService] Failed to delete GCS file (non-fatal): {e}")

        # 4. Delete the vectors from Pinecone
        try:
            from app.vector_store.pinecone_adapter import pinecone_adapter
            await pinecone_adapter.delete_document_vectors(str(project_id), str(document_id))
            logger.info(f"[DocumentService] Deleted Pinecone vectors | project={project_id} | document={document_id}")
        except Exception as e:
            logger.warning(f"[DocumentService] Failed to delete Pinecone vectors (non-fatal): {e}")

        # 4. Trigger Project Report Refresh to remove the document from the intelligence report
        try:
            import asyncio
            from app.services.project_service import ProjectService
            logger.info(f"[DocumentService] Triggering report refresh for project {project_id} after deletion of document {document_id}")
            asyncio.create_task(ProjectService.trigger_project_report_refresh(project_id))
        except Exception as e:
            logger.warning(f"[DocumentService] Failed to trigger report refresh (non-fatal): {e}")

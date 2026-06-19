from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.api.deps import require_project_role, get_current_user
from app.services.document_service import DocumentService

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    project_id: UUID,
    status: str | None = None,
    membership: ProjectMember = Depends(require_project_role(["admin", "member", "viewer"])),
    db: AsyncSession = Depends(get_db)
):
    return await DocumentService.list_documents(db, project_id, status_filter=status)

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_role(["admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    return await DocumentService.upload_document(db, project_id, file, current_user.user_id)

@router.post("/{document_id}/approve", response_model=DocumentResponse)
async def approve_document(
    project_id: UUID,
    document_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    return await DocumentService.approve_document(db, project_id, document_id)

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin", "member"])),
    db: AsyncSession = Depends(get_db)
):
    await DocumentService.delete_document(db, project_id, document_id)

from uuid import UUID
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse
from app.api.deps import get_current_user, require_project_role
from app.services.project_service import ProjectService

from typing import List, cast

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=List[ProjectResponse])
async def list_user_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.get_user_projects(db, cast(UUID, current_user.user_id))

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.create_project(db, project_in, cast(UUID, current_user.user_id))

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin", "member", "viewer"])),
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.get_project(db, project_id)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    await ProjectService.delete_project(db, project_id)

@router.get("/{project_id}/report")
async def get_project_report(
    project_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin", "member", "viewer"])),
):
    report = await ProjectService.get_project_report(project_id)
    if not report:
        from datetime import datetime, timezone
        return {
            "project_id": str(project_id),
            "document_count": 0,
            "modalities_included": [],
            "unified_summary": "No report available yet. Please upload documents to generate a project report.",
            "contradictions": [],
            "agreements": [],
            "cognitive_synthesis": {
                "intents": [],
                "reasoning_patterns": [],
                "assumptions": [],
                "conclusions": []
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    return report

@router.post("/{project_id}/report/refresh")
async def refresh_project_report(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    membership: ProjectMember = Depends(require_project_role(["admin", "member"])),
):
    background_tasks.add_task(ProjectService.trigger_project_report_refresh, project_id)
    return {"status": "refresh_triggered"}

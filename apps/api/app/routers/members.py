from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.member import MemberInvite, MemberResponse
from app.api.deps import require_project_role, get_current_user
from app.services.member_service import MemberService

router = APIRouter(prefix="/projects/{project_id}/members", tags=["members"])

@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: UUID,
    invite: MemberInvite,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    return await MemberService.add_member(db, project_id, invite, current_user.user_id)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: UUID,
    user_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    await MemberService.remove_member(db, project_id, user_id)

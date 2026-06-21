from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.member import MemberInvite, MemberResponse, InvitationResponse, RoleChangeRequest
from app.api.deps import require_project_role, get_current_user
from app.services.member_service import MemberService

router = APIRouter(prefix="/projects/{project_id}", tags=["members"])

@router.get("/members", response_model=List[MemberResponse])
async def list_members(
    project_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin", "member", "viewer"])),
    db: AsyncSession = Depends(get_db)
):
    return await MemberService.list_members(db, project_id)

@router.get("/invitations", response_model=List[InvitationResponse])
async def list_invitations(
    project_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin", "member", "viewer"])),
    db: AsyncSession = Depends(get_db)
):
    return await MemberService.list_invitations(db, project_id)

@router.post("/members", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: UUID,
    invite: MemberInvite,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    return await MemberService.add_member(db, project_id, invite, current_user.user_id)  # type: ignore

@router.patch("/members/{user_id}/role", response_model=MemberResponse)
async def update_role(
    project_id: UUID,
    user_id: UUID,
    request: RoleChangeRequest,
    membership: ProjectMember = Depends(require_project_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    pm = await MemberService.update_role(db, project_id, user_id, request.role)
    user = await db.get(User, user_id)
    return {
        "project_id": pm.project_id,
        "user_id": pm.user_id,
        "role": pm.role,
        "joined_at": pm.joined_at,
        "invited_by": pm.invited_by,
        "email": user.email if user else "",
        "name": user.name if user else None,
        "avatar_url": user.avatar_url if user else None
    }

@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: UUID,
    user_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    await MemberService.remove_member(db, project_id, user_id)

@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invitation(
    project_id: UUID,
    invitation_id: UUID,
    membership: ProjectMember = Depends(require_project_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    await MemberService.delete_invitation(db, project_id, invitation_id)

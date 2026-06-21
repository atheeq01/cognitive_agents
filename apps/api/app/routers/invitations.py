from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.schemas.member import MemberResponse, AcceptInviteRequest, UserInvitationResponse, DeclineInviteRequest
from app.api.deps import get_current_user
from app.services.member_service import MemberService

router = APIRouter(prefix="/invitations", tags=["invitations"])

@router.get("/me", response_model=List[UserInvitationResponse])
async def get_my_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # type checker sees current_user.email as Column[str] due to SQLAlchemy 1.4 declarative mapping
    return await MemberService.list_user_invitations(db, current_user.email)  # type: ignore

@router.post("/accept", response_model=MemberResponse)
async def accept_invitation(
    request: AcceptInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pm = await MemberService.accept_invitation(db, request.token, current_user)
    return {
        "project_id": pm.project_id,
        "user_id": pm.user_id,
        "role": pm.role,
        "joined_at": pm.joined_at,
        "invited_by": pm.invited_by,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url
    }

@router.post("/decline", status_code=204)
async def decline_invitation(
    request: DeclineInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await MemberService.decline_invitation(db, request.token, current_user)

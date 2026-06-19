from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.member import MemberResponse, AcceptInviteRequest
from app.api.deps import get_current_user
from app.services.member_service import MemberService

router = APIRouter(prefix="/invitations", tags=["invitations"])

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

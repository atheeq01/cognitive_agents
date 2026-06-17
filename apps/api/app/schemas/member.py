from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

RoleType = Literal["admin", "member", "viewer"]

class MemberInvite(BaseModel):
    email: str
    role: RoleType

class RoleChangeRequest(BaseModel):
    role: RoleType

class MemberResponse(BaseModel):
    project_id: UUID
    user_id: UUID
    email: str
    name: str | None = None
    avatar_url: str | None = None
    role: RoleType
    joined_at: datetime
    invited_by: UUID | None = None
    
    model_config = ConfigDict(from_attributes=True)

class InvitationResponse(BaseModel):
    id: UUID
    project_id: UUID
    email: str
    role: RoleType
    status: str
    invited_by: UUID | None = None
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AcceptInviteRequest(BaseModel):
    token: str

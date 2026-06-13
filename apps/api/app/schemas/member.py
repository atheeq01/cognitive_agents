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
    role: RoleType
    joined_at: datetime
    invited_by: UUID | None = None
    
    model_config = ConfigDict(from_attributes=True)

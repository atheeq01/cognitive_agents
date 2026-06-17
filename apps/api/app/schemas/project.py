from uuid import UUID
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    settings: Dict[str, Any] = {}
    upload_approval_required: bool = False
    legal_hold: bool = False

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    settings: Dict[str, Any] | None = None
    upload_approval_required: bool | None = None
    legal_hold: bool | None = None

class ProjectResponse(ProjectBase):
    project_id: UUID
    created_by: UUID
    created_at: datetime
    role: str | None = None
    
    model_config = ConfigDict(from_attributes=True)

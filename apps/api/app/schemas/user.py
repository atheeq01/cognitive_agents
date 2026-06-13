from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    email: str
    name: str | None = None
    avatar_url: str | None = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    user_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

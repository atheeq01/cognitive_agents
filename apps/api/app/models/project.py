import uuid
from datetime import datetime
from sqlalchemy import Column, String, JSON, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Per-project settings and workflows
    settings = Column(JSONB, default=dict)
    upload_approval_required = Column(Boolean, default=False)
    legal_hold = Column(Boolean, default=False)

    # Relationships
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

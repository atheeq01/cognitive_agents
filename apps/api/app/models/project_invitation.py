import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, text, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class ProjectInvitation(Base):
    __tablename__ = "project_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    email = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="pending")  # pending, accepted, declined
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), default=text("NOW() + INTERVAL '7 days'"))

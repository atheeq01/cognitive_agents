import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum

class DocumentStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    gcs_path = Column(String, nullable=False)
    
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING_APPROVAL)
    visibility = Column(String, default="project") # project, private
    privilege_status = Column(String, nullable=True) # attorney_client, etc.
    
    uploaded_at = Column(DateTime(timezone=True), default=func.now())

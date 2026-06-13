from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentStatus

class DocumentResponse(BaseModel):
    document_id: UUID
    project_id: UUID
    uploader_id: UUID | None
    filename: str
    mime_type: str
    size_bytes: int
    status: DocumentStatus
    visibility: str
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

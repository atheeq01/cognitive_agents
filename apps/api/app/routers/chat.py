from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel

from app.api.deps import require_project_role
from app.services.chat_service import chat_service

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

@router.post("")
async def chat_with_project(
    project_id: str,
    request: ChatRequest,
    _=Depends(require_project_role(["admin", "member", "viewer"]))
):
    """
    RAG Chat endpoint. Answers questions using documents isolated to the requested project.
    """
    try:
        # Convert history from Pydantic to list of dicts for the service
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        response = await chat_service.get_response(
            project_id=project_id,
            message=request.message,
            history=history_dicts
        )
        
        return {
            "answer": response.answer,
            "sources": response.sources
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chat response: {str(e)}"
        )

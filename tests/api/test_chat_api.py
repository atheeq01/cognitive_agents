import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

@pytest.mark.api
@pytest.mark.asyncio
class TestChatApi:
    async def test_chat_returns_answer(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project

        from unittest.mock import patch, AsyncMock
        from app.services.chat_service import ChatResponse

        with patch("app.routers.chat.chat_service.get_response", new_callable=AsyncMock) as mock_get_response:
            mock_get_response.return_value = ChatResponse(
                answer="Mocked answer",
                sources=[]
            )
            response = await api_client.post(
                f"/api/v1/projects/{project.project_id}/chat",
                json={"message": "What is the summary?"}
            )
        assert response.status_code == 200
        assert response.json()["answer"] == "Mocked answer"
        assert response.json()["sources"] == []

    async def test_chat_empty_message(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project

        from unittest.mock import patch, AsyncMock
        from app.services.chat_service import ChatResponse

        with patch("app.routers.chat.chat_service.get_response", new_callable=AsyncMock) as mock_get_response:
            mock_get_response.return_value = ChatResponse(
                answer="Empty response",
                sources=[]
            )
            response = await api_client.post(
                f"/api/v1/projects/{project.project_id}/chat",
                json={"message": ""}
            )
        assert response.status_code == 200

import pytest
from httpx import AsyncClient

@pytest.mark.api
@pytest.mark.asyncio
class TestAuth:
    async def test_no_auth_header(self, api_client: AsyncClient):
        original = api_client.headers.get("Authorization")
        if original:
            del api_client.headers["Authorization"]
            
        response = await api_client.get("/api/v1/projects")
        assert response.status_code in (401, 403)
        
        if original:
            api_client.headers["Authorization"] = original

    async def test_invalid_token(self, api_client: AsyncClient):
        original = api_client.headers.get("Authorization")
        api_client.headers["Authorization"] = "Bearer mock-expired"
        
        response = await api_client.get("/api/v1/projects")
        assert response.status_code == 401
        
        if original:
            api_client.headers["Authorization"] = original

    async def test_mock_token_in_local_mode(self, api_client: AsyncClient):
        # The api_client uses Bearer mock-admin@example.com by default
        response = await api_client.get("/api/v1/projects")
        assert response.status_code == 200

    async def test_auto_create_user(self, api_client: AsyncClient, db_session):
        # Make a request with a new email token
        original = api_client.headers.get("Authorization")
        api_client.headers["Authorization"] = "Bearer mock-newuser@example.com"
        
        response = await api_client.get("/api/v1/projects")
        assert response.status_code == 200
        
        # Verify user was created
        from sqlalchemy import select
        from app.models.user import User
        result = await db_session.execute(select(User).where(User.email == "newuser@example.com"))
        user = result.scalars().first()
        assert user is not None
        
        if original:
            api_client.headers["Authorization"] = original

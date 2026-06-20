import pytest
from httpx import AsyncClient

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_api_health_endpoint(api_client: AsyncClient):
    """Verify that the /health endpoint responds correctly."""
    # Temporarily remove auth header just for the health check
    original_auth = api_client.headers.get("Authorization")
    if "Authorization" in api_client.headers:
        del api_client.headers["Authorization"]
        
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    # Restore auth header
    if original_auth:
        api_client.headers["Authorization"] = original_auth

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_api_openapi_schema(api_client: AsyncClient):
    """Verify that the OpenAPI schema is available and parses correctly."""
    response = await api_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
    assert "/api/v1/projects" in schema["paths"]

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_unauthenticated_returns_403(api_client: AsyncClient):
    """Verify that API routes are protected."""
    original_auth = api_client.headers.get("Authorization")
    if "Authorization" in api_client.headers:
        del api_client.headers["Authorization"]
        
    response = await api_client.get("/api/v1/projects")
    # Our auth system might return 401 or 403 depending on the implementation
    assert response.status_code in (401, 403)
    
    if original_auth:
        api_client.headers["Authorization"] = original_auth

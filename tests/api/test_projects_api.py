import pytest
from httpx import AsyncClient

@pytest.mark.api
@pytest.mark.asyncio
class TestProjectsApi:
    async def test_create_project(self, api_client: AsyncClient):
        response = await api_client.post(
            "/api/v1/projects",
            json={"name": "API Project", "description": "API Desc"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Project"
        assert data["description"] == "API Desc"
        assert data["role"] == "admin"
        assert "project_id" in data

    async def test_create_project_minimal(self, api_client: AsyncClient):
        response = await api_client.post(
            "/api/v1/projects",
            json={"name": "API Project Minimal"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "API Project Minimal"

    async def test_list_projects_empty(self, api_client: AsyncClient):
        response = await api_client.get("/api/v1/projects")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_projects_returns_owned(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project
        response = await api_client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == project.name

    async def test_get_project_as_member(self, api_client: AsyncClient, mock_project, db_session):
        project, _ = mock_project
        from app.models.project_member import ProjectMember
        from app.models.user import User
        member_user = User(email="member@example.com", name="Member")
        db_session.add(member_user)
        await db_session.flush()
        pm = ProjectMember(project_id=project.project_id, user_id=member_user.user_id, role="member")
        db_session.add(pm)
        await db_session.commit()
        
        api_client.headers["Authorization"] = "Bearer mock-member@example.com"
        response = await api_client.get(f"/api/v1/projects/{project.project_id}")
        assert response.status_code == 200
        assert response.json()["name"] == project.name

    async def test_get_project_not_member(self, api_client: AsyncClient):
        import uuid
        response = await api_client.get(f"/api/v1/projects{uuid.uuid4()}")
        assert response.status_code == 404 # Project service raises 404 before we check membership in this case

    async def test_delete_project_as_admin(self, api_client: AsyncClient, mock_project, mock_user):
        project, _ = mock_project
        api_client.headers["Authorization"] = f"Bearer mock-{mock_user.email}"
        response = await api_client.delete(f"/api/v1/projects/{project.project_id}")
        assert response.status_code == 204

    async def test_get_report_no_data(self, api_client: AsyncClient, mock_project, mock_user):
        project, _ = mock_project
        api_client.headers["Authorization"] = f"Bearer mock-{mock_user.email}"
        response = await api_client.get(f"/api/v1/projects/{project.project_id}/report")
        assert response.status_code == 200
        assert response.json()["project_id"] == str(project.project_id)

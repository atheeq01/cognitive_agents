import pytest
from httpx import AsyncClient

@pytest.mark.api
@pytest.mark.asyncio
class TestMembersApi:
    async def test_list_members(self, api_client: AsyncClient, mock_project, mock_user):
        project, _ = mock_project
        response = await api_client.get(f"/api/v1/projects/{project.project_id}/members")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == mock_user.email
        assert data[0]["role"] == "admin"

    async def test_invite_member(self, api_client: AsyncClient, mock_project, db_session):
        project, _ = mock_project
        response = await api_client.post(
            f"/api/v1/projects/{project.project_id}/members",
            json={"email": "new@test.com", "role": "member"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@test.com"
        assert data["role"] == "member"
        
        from sqlalchemy import select
        from app.models.project_invitation import ProjectInvitation
        result = await db_session.execute(select(ProjectInvitation).where(ProjectInvitation.email == "new@test.com"))
        inv = result.scalars().first()
        return inv.token # For use in other tests

    async def test_invite_duplicate_email(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project
        await api_client.post(
            f"/api/v1/projects/{project.project_id}/members",
            json={"email": "dup@test.com", "role": "member"}
        )
        response = await api_client.post(
            f"/api/v1/projects/{project.project_id}/members",
            json={"email": "dup@test.com", "role": "member"}
        )
        assert response.status_code == 400

    async def test_invite_existing_member(self, api_client: AsyncClient, mock_project, mock_user):
        project, _ = mock_project
        response = await api_client.post(
            f"/api/v1/projects/{project.project_id}/members",
            json={"email": mock_user.email, "role": "viewer"}
        )
        assert response.status_code == 400

    async def test_update_role(self, api_client: AsyncClient, mock_project, mock_user):
        project, _ = mock_project
        response = await api_client.patch(
            f"/api/v1/projects/{project.project_id}/members/{mock_user.user_id}/role",
            json={"role": "viewer"}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "viewer"

    async def test_remove_member(self, api_client: AsyncClient, mock_project, mock_user):
        project, _ = mock_project
        response = await api_client.delete(
            f"/api/v1/projects/{project.project_id}/members/{mock_user.user_id}"
        )
        assert response.status_code == 204

@pytest.mark.api
@pytest.mark.asyncio
class TestInvitationsApi:
    async def test_accept_invitation(self, api_client: AsyncClient, db_session, mock_project):
        # 1. Invite
        project, _ = mock_project
        resp = await api_client.post(
            f"/api/v1/projects/{project.project_id}/members",
            json={"email": "accept@test.com", "role": "viewer"}
        )
        from sqlalchemy import select
        from app.models.project_invitation import ProjectInvitation
        result = await db_session.execute(select(ProjectInvitation).where(ProjectInvitation.email == "accept@test.com"))
        token = result.scalars().first().token
        
        # 2. Accept (as the invited user)
        api_client.headers["Authorization"] = "Bearer mock-accept@test.com"
        
        response = await api_client.post(
            "/api/v1/invitations/accept",
            json={"token": token}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "viewer"

    async def test_accept_wrong_email(self, api_client: AsyncClient, db_session, mock_project):
        project, _ = mock_project
        resp = await api_client.post(
            f"/api/v1/projects/{project.project_id}/members",
            json={"email": "accept1@test.com", "role": "viewer"}
        )
        from sqlalchemy import select
        from app.models.project_invitation import ProjectInvitation
        result = await db_session.execute(select(ProjectInvitation).where(ProjectInvitation.email == "accept1@test.com"))
        token = result.scalars().first().token
        
        # Accept as a different user
        api_client.headers["Authorization"] = "Bearer mock-accept2@test.com"
        
        response = await api_client.post(
            "/api/v1/invitations/accept",
            json={"token": token}
        )
        assert response.status_code == 400
        assert "different email" in response.json()["detail"].lower()

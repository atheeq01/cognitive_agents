import pytest
from app.services.project_service import ProjectService
from app.services.member_service import MemberService
from app.schemas.project import ProjectCreate

@pytest.mark.db
@pytest.mark.asyncio
class TestServiceDBIntegration:
    async def test_create_project_adds_admin_member(self, db_session, mock_user):
        project_in = ProjectCreate(name="Service Proj")
        p = await ProjectService.create_project(db_session, project_in, mock_user.user_id)
        
        assert p.name == "Service Proj"
        assert p.role == "admin"
        
        # Verify db has the member
        projs = await ProjectService.get_user_projects(db_session, mock_user.user_id)
        assert len(projs) == 1
        assert projs[0].project_id == p.project_id
        assert projs[0].role == "admin"

    async def test_delete_project_cascades(self, db_session, mock_user):
        project_in = ProjectCreate(name="Service Proj Del")
        p = await ProjectService.create_project(db_session, project_in, mock_user.user_id)
        
        await ProjectService.delete_project(db_session, p.project_id)
        
        projs = await ProjectService.get_user_projects(db_session, mock_user.user_id)
        assert len(projs) == 0

    async def test_add_member_creates_invitation(self, db_session, mock_project, mock_user):
        project, _ = mock_project
        
        from app.schemas.member import MemberInvite
        inv = await MemberService.add_member(
            db_session, project.project_id, MemberInvite(email="invite@test.com", role="viewer"), mock_user.user_id
        )
        
        assert inv.email == "invite@test.com"
        assert inv.role == "viewer"
        assert inv.token is not None

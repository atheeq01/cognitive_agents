import pytest
import datetime
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.document import Document, DocumentStatus
from app.models.project_invitation import ProjectInvitation

@pytest.mark.db
@pytest.mark.asyncio
class TestModels:
    async def test_user_create(self, db_session):
        u = User(email="t1@test.com", name="T1")
        db_session.add(u)
        await db_session.flush()
        assert u.user_id is not None
        assert u.created_at is not None

    async def test_user_unique_email(self, db_session):
        u1 = User(email="dup@test.com", name="T1")
        u2 = User(email="dup@test.com", name="T2")
        db_session.add(u1)
        await db_session.flush()
        db_session.add(u2)
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_project_create(self, db_session, mock_user):
        p = Project(name="Test Proj", created_by=mock_user.user_id, settings={"x": 1})
        db_session.add(p)
        await db_session.flush()
        assert p.project_id is not None
        assert p.settings == {"x": 1}

    async def test_project_member_composite_pk(self, db_session, mock_project, mock_user):
        project, member = mock_project
        # Add again
        m2 = ProjectMember(project_id=project.project_id, user_id=mock_user.user_id, role="viewer")
        db_session.add(m2)
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_project_member_role_constraint(self, db_session, mock_project, mock_user):
        project, _ = mock_project
        u2 = User(email="u2@test.com", name="T2")
        db_session.add(u2)
        await db_session.flush()
        
        m = ProjectMember(project_id=project.project_id, user_id=u2.user_id, role="invalid")
        db_session.add(m)
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_document_status_enum(self, db_session, mock_project, mock_user):
        project, _ = mock_project
        doc = Document(
            project_id=project.project_id,
            uploader_id=mock_user.user_id,
            filename="test.txt",
            mime_type="text/plain",
            size_bytes=100,
            gcs_path="gs://...",
            status=DocumentStatus.PENDING_APPROVAL
        )
        db_session.add(doc)
        await db_session.flush()
        assert doc.status == DocumentStatus.PENDING_APPROVAL

    async def test_invitation_default_expiry(self, db_session, mock_project, mock_user):
        project, _ = mock_project
        inv = ProjectInvitation(
            project_id=project.project_id,
            email="inv@test.com",
            role="member",
            invited_by=mock_user.user_id,
            token="dummy-token-123"
        )
        db_session.add(inv)
        await db_session.flush()
        assert inv.expires_at.replace(tzinfo=None) > datetime.datetime.utcnow() + datetime.timedelta(days=6)

    async def test_invitation_unique_token(self, db_session, mock_project, mock_user):
        project, _ = mock_project
        inv1 = ProjectInvitation(
            project_id=project.project_id, email="inv1@test.com", role="member",
            invited_by=mock_user.user_id, token="token-123"
        )
        inv2 = ProjectInvitation(
            project_id=project.project_id, email="inv2@test.com", role="member",
            invited_by=mock_user.user_id, token="token-123"
        )
        db_session.add(inv1)
        await db_session.flush()
        db_session.add(inv2)
        with pytest.raises(IntegrityError):
            await db_session.flush()

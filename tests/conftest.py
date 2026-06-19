import pytest
import os
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from httpx import AsyncClient

# Patch environment BEFORE importing the app or db
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:1234@localhost:5432/omnimind_test"

from app.db.base import Base
from app.db.session import engine as app_engine
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from apps.api.main import app

# URL for creating the test DB connects to the default `postgres` db
SYS_DB_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/postgres"
TEST_DB_URL = os.environ["DATABASE_URL"]
TEST_DB_NAME = "omnimind_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database, run migrations, yield engine, then tear down."""
    sys_engine = create_async_engine(SYS_DB_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with sys_engine.connect() as conn:
        # Terminate connections to test DB if it exists
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid();
        """))
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    await sys_engine.dispose()

    test_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    await test_engine.dispose()
    
    # Optional teardown:
    # sys_engine = create_async_engine(SYS_DB_URL, isolation_level="AUTOCOMMIT")
    # async with sys_engine.connect() as conn:
    #     await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
    # await sys_engine.dispose()


@pytest.fixture
async def db_session(test_db_engine):
    """
    Returns an sqlalchemy session, and after the test tears down everything properly.
    Uses transaction rollback strategy to keep tests fast and isolated.
    """
    connection = await test_db_engine.connect()
    transaction = await connection.begin()
    
    SessionLocal = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
    session = SessionLocal()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()

# Mock overrides
@pytest.fixture
def mock_firebase_token(monkeypatch):
    async def mock_verify(cred_or_token):
        token = getattr(cred_or_token, "credentials", cred_or_token)
        if token == "mock-expired":
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Token expired")
        if not token.startswith("mock-"):
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid token")
        email = token.replace("mock-", "")
        return {"email": email, "name": "Test User", "uid": "test-uid-123"}
    
    # We patch the verify function in security.py
    monkeypatch.setattr("app.core.security.verify_firebase_token", mock_verify)
    try:
        monkeypatch.setattr("app.api.deps.verify_firebase_token", mock_verify)
    except AttributeError:
        pass

@pytest.fixture
def mock_storage(monkeypatch):
    async def mock_upload(*args, **kwargs):
        return "gs://omnimind-documents-test/mock-path.pdf"
    
    monkeypatch.setattr("app.services.storage_service.StorageService.upload_document", mock_upload)

@pytest.fixture
def mock_pubsub(monkeypatch):
    async def mock_pub_doc(*args, **kwargs):
        pass
    async def mock_pub_mem(*args, **kwargs):
        pass
    monkeypatch.setattr("app.services.pubsub_service.PubSubService.publish_document_approved", mock_pub_doc)
    monkeypatch.setattr("app.services.pubsub_service.PubSubService.publish_member_accepted", mock_pub_mem)
    monkeypatch.setattr("app.services.pubsub_service.PubSubService.publish_member_invited", mock_pub_mem)
    monkeypatch.setattr("app.services.pubsub_service.PubSubService.publish_role_changed", mock_pub_mem)

@pytest.fixture
async def api_client(db_session, mock_firebase_token, mock_storage, mock_pubsub):
    """httpx.AsyncClient targeting the FastAPI app with the test DB session injected."""
    
    # We need to override the get_db dependency
    from app.api.deps import get_db
    
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Default user auth
        client.headers.update({"Authorization": "Bearer mock-admin@example.com"})
        yield client
        
    app.dependency_overrides.clear()

@pytest.fixture
async def mock_user(db_session) -> User:
    """Creates a seeded mock user in the DB."""
    user = User(
        email="admin@example.com",
        name="Admin User"
    )
    db_session.add(user)
    await db_session.flush()
    return user

@pytest.fixture
async def mock_project(db_session, mock_user) -> tuple[Project, ProjectMember]:
    """Creates a seeded mock project with the mock_user as admin."""
    project = Project(
        name="Test RAG Project",
        created_by=mock_user.user_id
    )
    db_session.add(project)
    await db_session.flush()
    
    member = ProjectMember(
        project_id=project.project_id,
        user_id=mock_user.user_id,
        role="admin"
    )
    db_session.add(member)
    await db_session.flush()
    return project, member

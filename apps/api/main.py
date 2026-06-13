from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.routers import projects, members, documents

from app.db.session import engine
from app.db.base import Base

from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.document import Document

# Suppress linter warnings for "unused" imports
__models__ = [User, Project, ProjectMember, Document]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This block runs on server startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # This block runs on server shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Includes the routers
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(members.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok"}

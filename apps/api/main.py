import warnings
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Suppress harmless aiohttp task cancellation warnings from Langchain / Google GenAI SDKs
warnings.filterwarnings("ignore", message="coroutine 'ClientResponse.json' was never awaited", category=RuntimeWarning)

# Suppress noisy google_genai logs
logging.getLogger("google_genai").setLevel(logging.WARNING)

from app.core.config import settings
from app.routers import projects, members, documents, chat, invitations

from app.db.session import engine
from app.db.base import Base

from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.document import Document
from app.models.project_invitation import ProjectInvitation

__models__ = [User, Project, ProjectMember, ProjectInvitation, Document]

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includes the routers
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(members.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(invitations.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok"}

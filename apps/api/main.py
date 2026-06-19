from dotenv import load_dotenv
load_dotenv()
import warnings
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()],
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

from sqlalchemy import text

@app.get("/health")
async def health_check():
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"
        
    return {
        "status": "ok" if db_status == "ok" else "error",
        "database": db_status
    }

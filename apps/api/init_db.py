import asyncio
from app.db.base import Base
from app.db.session import engine

# Import all models here so they are registered with Base.metadata
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_invitation import ProjectInvitation
from app.models.document import Document

# Suppress linter warnings for "unused" imports
__models__ = [User, Project, ProjectMember, ProjectInvitation, Document]

async def init_models():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("Successfully created database tables!")

if __name__ == "__main__":
    asyncio.run(init_models())

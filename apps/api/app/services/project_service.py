from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.schemas.project import ProjectCreate

class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, project_in: ProjectCreate, user_id: UUID) -> Project:
        project = Project(
            name=project_in.name,
            description=project_in.description,
            settings=project_in.settings,
            upload_approval_required=project_in.upload_approval_required,
            legal_hold=project_in.legal_hold,
            created_by=user_id
        )
        db.add(project)
        await db.flush()
        
        member = ProjectMember(
            project_id=project.project_id,
            user_id=user_id,
            role="admin"
        )
        db.add(member)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def get_project(db: AsyncSession, project_id: UUID) -> Project:
        result = await db.execute(select(Project).where(Project.project_id == project_id))
        project = result.scalars().first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    @staticmethod
    async def delete_project(db: AsyncSession, project_id: UUID) -> None:
        project = await ProjectService.get_project(db, project_id)
        await db.delete(project)
        await db.commit()

    @staticmethod
    async def get_user_projects(db: AsyncSession, user_id: UUID) -> list[Project]:
        result = await db.execute(
            select(Project, ProjectMember.role)
            .join(ProjectMember, Project.project_id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user_id)
        )
        projects = []
        for p, role in result.all():
            p.role = role
            projects.append(p)
        return projects

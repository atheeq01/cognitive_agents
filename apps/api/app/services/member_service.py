from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.member import MemberInvite

class MemberService:
    @staticmethod
    async def list_members(db: AsyncSession, project_id: UUID) -> list[ProjectMember]:
        result = await db.execute(
            select(ProjectMember).where(ProjectMember.project_id == project_id)
        )
        return result.scalars().all()

    @staticmethod
    async def add_member(db: AsyncSession, project_id: UUID, invite: MemberInvite, invited_by: UUID) -> ProjectMember:
        result = await db.execute(select(User).where(User.email == invite.email))
        target_user = result.scalars().first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        mem_result = await db.execute(select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user.user_id
        ))
        if mem_result.scalars().first():
            raise HTTPException(status_code=400, detail="User already in project")
            
        new_member = ProjectMember(
            project_id=project_id,
            user_id=target_user.user_id,
            role=invite.role,
            invited_by=invited_by
        )
        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)
        return new_member

    @staticmethod
    async def remove_member(db: AsyncSession, project_id: UUID, user_id: UUID) -> None:
        result = await db.execute(select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ))
        member = result.scalars().first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
            
        await db.delete(member)
        await db.commit()

from uuid import UUID
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.project_invitation import ProjectInvitation
from app.schemas.member import MemberInvite
from app.services.pubsub_service import pubsub_service

class MemberService:
    @staticmethod
    async def list_members(db: AsyncSession, project_id: UUID) -> list[dict]:
        stmt = (
            select(ProjectMember, User)
            .join(User, ProjectMember.user_id == User.user_id)
            .where(ProjectMember.project_id == project_id)
        )
        result = await db.execute(stmt)
        members = []
        for pm, user in result.all():
            members.append({
                "project_id": pm.project_id,
                "user_id": pm.user_id,
                "role": pm.role,
                "joined_at": pm.joined_at,
                "invited_by": pm.invited_by,
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url
            })
        return members

    @staticmethod
    async def list_invitations(db: AsyncSession, project_id: UUID) -> list[ProjectInvitation]:
        result = await db.execute(
            select(ProjectInvitation)
            .where(ProjectInvitation.project_id == project_id, ProjectInvitation.status == "pending")
        )
        return result.scalars().all()

    @staticmethod
    async def add_member(db: AsyncSession, project_id: UUID, invite: MemberInvite, invited_by: UUID) -> ProjectInvitation:
        # Check if already a member
        user_result = await db.execute(select(User).where(User.email == invite.email))
        target_user = user_result.scalars().first()
        
        if target_user:
            mem_result = await db.execute(select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == target_user.user_id
            ))
            if mem_result.scalars().first():
                raise HTTPException(status_code=400, detail="User already in project")
                
        # Check if an invitation already exists
        inv_result = await db.execute(select(ProjectInvitation).where(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.email == invite.email,
            ProjectInvitation.status == "pending"
        ))
        if inv_result.scalars().first():
            raise HTTPException(status_code=400, detail="User already invited")
            
        token = secrets.token_urlsafe(32)
        new_invitation = ProjectInvitation(
            project_id=project_id,
            email=invite.email,
            role=invite.role,
            token=token,
            invited_by=invited_by
        )
        db.add(new_invitation)
        await db.commit()
        await db.refresh(new_invitation)
        
        # Publish event
        await pubsub_service.publish_member_invited(str(project_id), invite.email, invite.role)
        
        return new_invitation

    @staticmethod
    async def accept_invitation(db: AsyncSession, token: str, current_user: User) -> ProjectMember:
        result = await db.execute(select(ProjectInvitation).where(ProjectInvitation.token == token))
        invitation = result.scalars().first()
        
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found or invalid")
            
        if invitation.status != "pending":
            raise HTTPException(status_code=400, detail="Invitation already processed")
            
        if current_user.email != invitation.email:
            raise HTTPException(status_code=400, detail="This invitation was sent to a different email address")
            
        # Check if already in project (in case they somehow joined)
        mem_result = await db.execute(select(ProjectMember).where(
            ProjectMember.project_id == invitation.project_id,
            ProjectMember.user_id == current_user.user_id
        ))
        if mem_result.scalars().first():
            invitation.status = "accepted"
            await db.commit()
            raise HTTPException(status_code=400, detail="You are already in this project")
            
        # Create member
        new_member = ProjectMember(
            project_id=invitation.project_id,
            user_id=current_user.user_id,
            role=invitation.role,
            invited_by=invitation.invited_by
        )
        db.add(new_member)
        
        # Update invitation
        invitation.status = "accepted"
        
        await db.commit()
        await db.refresh(new_member)
        
        # Publish event
        await pubsub_service.publish_member_accepted(str(invitation.project_id), str(current_user.user_id))
        
        return new_member

    @staticmethod
    async def update_role(db: AsyncSession, project_id: UUID, user_id: UUID, new_role: str) -> ProjectMember:
        result = await db.execute(select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ))
        member = result.scalars().first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
            
        member.role = new_role
        await db.commit()
        await db.refresh(member)
        
        # Publish event
        await pubsub_service.publish_role_changed(str(project_id), str(user_id), new_role)
        
        return member

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

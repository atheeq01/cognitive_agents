from typing import Annotated, Callable
from uuid import UUID
from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import security, verify_firebase_token
from app.db.session import get_db
from app.models.user import User
from app.models.project_member import ProjectMember

async def get_current_user(
    cred: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    token_payload = await verify_firebase_token(cred)
    email = token_payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Token missing email")
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        try:
            user = User(email=email, name=token_payload.get("name"))
            db.add(user)
            await db.commit()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=500, detail="Failed to create or retrieve user")
        
    return user

def require_project_role(required_roles: list[str]) -> Callable:
    """
    Dependency generator for RBAC. Enforces that the current user
    has one of the required roles in the specified project.
    Also injects the project_id into the PostgreSQL session context for RLS.
    
    NOTE: This dependency uses the SAME `db` session as the route handler
    (FastAPI de-duplicates identical Depends() calls within a request),
    so the `SET LOCAL` RLS config will be visible to subsequent queries
    in the handler.
    """
    async def role_checker(
        project_id: UUID = Path(...),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> ProjectMember:
        await db.execute(
            text("SELECT set_config('app.project_id', :project_id, true)").bindparams(project_id=str(project_id))
        )
        result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.user_id
            )
        )
        membership = result.scalars().first()
        
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this project")
            
        if membership.role not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
            
        return membership
        
    return role_checker

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
        
        # Attach role for response serialization
        project.role = "admin"
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

    @staticmethod
    async def get_project_report(project_id: UUID) -> dict | None:
        from app.core.firebase import init_firebase
        from firebase_admin import firestore as fb_firestore
        import asyncio
        
        init_firebase()
        fs_client = fb_firestore.client()
        report_ref = fs_client.collection("projects").document(str(project_id))
        doc = await asyncio.to_thread(report_ref.get)
        if doc.exists:
            data = doc.to_dict()
            return data.get("project_report")
        return None

    @staticmethod
    async def trigger_project_report_refresh(project_id: UUID) -> None:
        from app.core.firebase import init_firebase
        from firebase_admin import firestore as fb_firestore
        from datetime import datetime, timezone
        from app.agents.contradiction_pipeline.project_synthesis_agent import project_synthesis_agent
        from app.vector_store.pinecone_adapter import pinecone_adapter
        from google.cloud.firestore_v1.base_query import FieldFilter
        import asyncio
        
        init_firebase()
        fs_client = fb_firestore.client()
        
        query = fs_client.collection("projects").document(str(project_id)).collection("jobs").where(filter=FieldFilter("status", "==", "completed"))
        def _stream():
            return list(query.stream())
        docs = await asyncio.to_thread(_stream)
        
        valid_doc_ids = set()
        docs_list = []
        for d in docs:
            valid_doc_ids.add(d.id)
            docs_list.append(d.to_dict())

        all_claims = []
        for d in docs_list:
            doc_claims = d.get("results", {}).get("claims", [])
            for c in doc_claims:
                all_claims.append({
                    "fact": c.get("fact"),
                    "source_location": c.get("source_location")
                })
                
        if not all_claims:
            pinecone_claims = await pinecone_adapter.fetch_all(str(project_id), type="claim")
            all_claims = [c for c in pinecone_claims if c.get("document_id") in valid_doc_ids]

        report = await project_synthesis_agent.synthesize(str(project_id), docs_list, all_claims)

        def _set_report():
            if report:
                fs_client.collection("projects").document(str(project_id)).set({
                    "project_report": report,
                    "last_synthesized_at": datetime.now(timezone.utc).isoformat()
                }, merge=True)
            else:
                fs_client.collection("projects").document(str(project_id)).set({
                    "project_report": {
                        "project_id": str(project_id),
                        "document_count": 0,
                        "modalities_included": [],
                        "unified_summary": "No documents in project.",
                        "contradictions": [],
                        "agreements": [],
                        "cognitive_synthesis": {"intents": [], "reasoning_patterns": [], "assumptions": [], "conclusions": []},
                        "generated_at": datetime.now(timezone.utc).isoformat()
                    },
                    "last_synthesized_at": datetime.now(timezone.utc).isoformat()
                }, merge=True)
                
        await asyncio.to_thread(_set_report)

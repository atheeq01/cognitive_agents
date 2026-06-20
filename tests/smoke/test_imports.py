import pytest

@pytest.mark.smoke
def test_import_api_main():
    """Verify that the FastAPI app for the API server can be imported without crashing."""
    try:
        from apps.api.main import app
        assert app is not None
        assert app.title == "OmniMind v2 Local API"
    except Exception as e:
        pytest.fail(f"Failed to import API main app: {e}")

@pytest.mark.smoke
def test_import_worker_main():
    """Verify that the FastAPI app for the Worker server can be imported without crashing."""
    try:
        from apps.worker.main import app
        assert app is not None
    except Exception as e:
        pytest.fail(f"Failed to import Worker main app: {e}")

@pytest.mark.smoke
def test_import_all_models():
    """Verify that all SQLAlchemy models can be imported successfully."""
    try:
        from app.models.user import User
        from app.models.project import Project
        from app.models.project_member import ProjectMember
        from app.models.project_invitation import ProjectInvitation
        from app.models.document import Document
        
        assert User.__tablename__ == "users"
        assert Project.__tablename__ == "projects"
        assert ProjectMember.__tablename__ == "project_members"
        assert ProjectInvitation.__tablename__ == "project_invitations"
        assert Document.__tablename__ == "documents"
    except Exception as e:
        pytest.fail(f"Failed to import models: {e}")

@pytest.mark.smoke
def test_import_all_schemas():
    """Verify that all Pydantic schemas can be imported successfully."""
    try:
        from app.schemas.project import ProjectCreate, ProjectResponse
        from app.schemas.user import UserCreate, UserResponse
        from app.schemas.member import MemberResponse, MemberInvite
        from app.schemas.report import ProjectReport, ContradictionFinding
        
        # Pydantic v2 has model_fields
        assert hasattr(ProjectCreate, "model_fields")
        assert hasattr(ProjectReport, "model_fields")
    except Exception as e:
        pytest.fail(f"Failed to import schemas: {e}")

@pytest.mark.smoke
def test_import_pipeline_agents():
    """Verify that the Cognitive pipeline and its agents can be imported."""
    try:
        from app.agents.pipeline import BaseAgent, AgentPipeline
        from app.agents.contradiction_pipeline.nli_classifier import NLIClassifier
        from app.agents.contradiction_pipeline.verification_pass import VerificationPass
        from app.agents.contradiction_pipeline.project_synthesis_agent import ProjectSynthesisAgent
        from app.agents.contradiction_pipeline.candidate_selector import CandidateSelector
        
        assert issubclass(NLIClassifier, BaseAgent)
    except Exception as e:
        pytest.fail(f"Failed to import pipeline agents: {e}")

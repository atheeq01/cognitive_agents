import pytest
from pydantic import ValidationError
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.member import MemberInvite
from app.schemas.report import SourceLocation, ContradictionFinding, ProjectReport

@pytest.mark.unit
class TestSchemas:
    def test_project_create_minimal(self):
        p = ProjectCreate(name="Test")
        assert p.name == "Test"
        assert p.description is None
        assert p.settings == {}
        
    def test_project_create_full(self):
        p = ProjectCreate(name="Test", description="Desc", settings={"a": 1})
        assert p.description == "Desc"
        assert p.settings["a"] == 1
        
    def test_project_response_from_attributes(self):
        from datetime import datetime
        import uuid
        class MockOrm:
            project_id = "123e4567-e89b-12d3-a456-426614174000"
            name = "Test"
            description = None
            settings = {}
            created_at = datetime.now()
            created_by = uuid.uuid4()
            role = "admin"
            
        p = ProjectResponse.model_validate(MockOrm(), from_attributes=True)
        assert p.name == "Test"
        assert p.role == "admin"
        
    def test_member_invite_role_validation(self):
        inv = MemberInvite(email="test@test.com", role="admin")
        assert inv.role == "admin"
        
    def test_member_invite_invalid_role(self):
        with pytest.raises(ValidationError):
            MemberInvite(email="test@test.com", role="superadmin")
            
    def test_source_location_modality_validation(self):
        sl = SourceLocation(document_id="1", document_name="doc1", modality="pdf", exact_quote="hi")
        assert sl.modality == "pdf"
        
        with pytest.raises(ValidationError):
            SourceLocation(document_id="1", document_name="doc1", modality="invalid", exact_quote="hi")
        
    def test_contradiction_finding_required_fields(self):
        with pytest.raises(ValidationError):
            # Missing fields
            ContradictionFinding(severity="HIGH")
            
    def test_project_report_serialization(self):
        from datetime import datetime
        r = ProjectReport(
            project_id="test",
            document_count=1,
            modalities_included=["pdf"],
            unified_summary="Sum",
            cognitive_synthesis={"intents": []},
            contradictions=[],
            agreements=[],
            generated_at=datetime.now()
        )
        data = r.model_dump()
        assert data["project_id"] == "test"
        
        r2 = ProjectReport.model_validate(data)
        assert r2.document_count == 1

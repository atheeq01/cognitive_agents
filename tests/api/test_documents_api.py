import pytest
from httpx import AsyncClient
import io

@pytest.mark.api
@pytest.mark.asyncio
class TestDocumentsApi:
    async def test_upload_pdf(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project
        
        # We need a multipart request
        file_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"
        files = {"file": ("test.pdf", file_content, "application/pdf")}
        
        response = await api_client.post(
            f"/api/v1/projects/{project.project_id}/documents",
            files=files
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["status"] == "approved"

    async def test_upload_too_large(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project
        
        # Simulate a 51MB file
        file_content = b"0" * (51 * 1024 * 1024)
        files = {"file": ("big.txt", file_content, "text/plain")}
        
        response = await api_client.post(
            f"/api/v1/projects/{project.project_id}/documents",
            files=files
        )
        assert response.status_code == 413

    async def test_upload_unsupported_type(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project
        
        file_content = b"MZ\x00\x00\x00\x00" # EXE signature
        files = {"file": ("bad.exe", file_content, "application/x-msdownload")}
        
        from unittest.mock import patch
        with patch("app.services.document_service.magic.from_buffer", return_value="application/x-msdownload"):
            response = await api_client.post(
                f"/api/v1/projects/{project.project_id}/documents",
                files=files
            )
        assert response.status_code == 415

    async def test_list_documents_empty(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project
        response = await api_client.get(f"/api/v1/projects/{project.project_id}/documents")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_documents_invalid_status(self, api_client: AsyncClient, mock_project):
        project, _ = mock_project
        response = await api_client.get(f"/api/v1/projects/{project.project_id}/documents?status=invalid")
        assert response.status_code == 400

    async def test_delete_document_not_found(self, api_client: AsyncClient, mock_project):
        import uuid
        project, _ = mock_project
        response = await api_client.delete(f"/api/v1/projects/{project.project_id}/documents/{uuid.uuid4()}")
        assert response.status_code == 404

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DocumentAIProcessor:
    def __init__(self):
        self.mock_mode = False
        try:
            from google.cloud import documentai
            self.client = documentai.DocumentProcessorServiceClient()
            # In a real scenario, the processor_name would come from config
            self.processor_name = "projects/mock/locations/us/processors/mock"
        except Exception as e:
            logger.warning(f"Failed to initialize Google Document AI. Running in mock mode: {e}")
            self.mock_mode = True

    async def process_document(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Processes PDF/DOCX using Document AI to extract layout structure, paragraphs, and tables.
        Returns a dict that can be digested by UCDBuilder.
        """
        if self.mock_mode:
            logger.info(f"[MOCK DOC_AI] Processing {mime_type} document of size {len(file_bytes)} bytes")
            return {
                "raw_text": "This is a mocked Document AI extracted text.\n\nSection 1\nIt has tables and structure.",
                "page_count": 1,
                "tables_found": 1,
                "modality": "pdf" if "pdf" in mime_type else "docx"
            }

        try:
            from google.cloud import documentai
            
            raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            # Since documentai client is synchronous, we'd typically wrap this in run_in_executor
            # but for this architecture, we keep it simple here.
            result = self.client.process_document(request=request)
            document = result.document
            
            # Very basic extraction mapping
            return {
                "raw_text": document.text,
                "page_count": len(document.pages),
                "tables_found": sum(len(page.tables) for page in document.pages),
                "modality": "pdf" if "pdf" in mime_type else "docx"
            }
        except Exception as e:
            logger.error(f"Failed to process document with Document AI: {e}")
            raise

document_ai_processor = DocumentAIProcessor()

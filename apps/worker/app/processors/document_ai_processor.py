import logging
import os
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Models to try in order — if one is overloaded (503), try the next
GEMINI_FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]


class DocumentAIProcessor:
    def __init__(self):
        self.docai_available = False
        try:
            from google.cloud import documentai

            project_id = os.environ.get("DOCAI_PROJECT_ID") or os.environ.get("FIREBASE_PROJECT_ID") or "mock"
            location = os.environ.get("DOCAI_LOCATION") or "us"
            processor_id = os.environ.get("DOCAI_PROCESSOR_ID") or "mock"

            self.processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

            if "mock" in self.processor_name:
                logger.warning(f"Document AI configured with mock values: {self.processor_name}. Will use Gemini fallback.")
            else:
                self.client = documentai.DocumentProcessorServiceClient()
                self.docai_available = True
                logger.info(f"[DocumentAI] Initialized | processor={self.processor_name}")
        except Exception as e:
            logger.warning(f"Document AI not available: {e}. Will use Gemini fallback.")

    def _split_pdf_if_needed(self, file_bytes: bytes, mime_type: str, max_pages: int = 30) -> list[bytes]:
        if "pdf" not in mime_type.lower():
            return [file_bytes]
            
        try:
            import fitz
            fitz.TOOLS.mupdf_display_errors(False)
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            if len(doc) <= max_pages:
                return [file_bytes]
                
            chunks = []
            for i in range(0, len(doc), max_pages):
                chunk_doc = fitz.open()
                chunk_doc.insert_pdf(doc, from_page=i, to_page=min(i + max_pages - 1, len(doc) - 1))
                chunks.append(chunk_doc.tobytes())
                chunk_doc.close()
            doc.close()
            return chunks
        except Exception as e:
            logger.warning(f"Failed to split PDF, proceeding with original: {e}")
            return [file_bytes]

    async def process_document(self, file_bytes: bytes, mime_type: str, gcs_path: Optional[str] = None, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes PDF/DOCX to extract text.
        Strategy:
          1. Try Document AI (if available and configured with real credentials)
          2. Fallback: Use Gemini Vision to extract text from the file bytes
        """
        doc_id_label = document_id or "unknown"

        # --- Attempt 1: Document AI (if available) ---
        if self.docai_available:
            try:
                chunks = self._split_pdf_if_needed(file_bytes, mime_type, max_pages=30)
                
                if len(chunks) == 1:
                    result = await self._extract_with_docai(chunks[0], mime_type, gcs_path, document_id)
                else:
                    logger.info(f"[DocumentAI] Document > 30 pages. Split into {len(chunks)} chunks.")
                    results = []
                    for i, chunk_bytes in enumerate(chunks):
                        logger.info(f"[DocumentAI] Processing chunk {i+1}/{len(chunks)}")
                        res = await self._extract_with_docai(chunk_bytes, mime_type, gcs_path, document_id)
                        results.append(res)
                    
                    merged_text = "\n\n".join(r.get("raw_text", "") for r in results)
                    
                    merged_pages = []
                    page_offset = 0
                    for r in results:
                        for p in r.get("pages", []):
                            merged_pages.append({
                                "page_number": p["page_number"] + page_offset,
                                "text": p["text"]
                            })
                        page_offset += r.get("page_count", 0)
                        
                    result = {
                        "raw_text": merged_text,
                        "pages": merged_pages,
                        "page_count": sum(r.get("page_count", 0) for r in results),
                        "tables_found": sum(r.get("tables_found", 0) for r in results),
                        "modality": results[0].get("modality", "pdf") if results else "pdf"
                    }

                if result.get("raw_text", "").strip():
                    logger.info(f"[DocumentAI] Extraction succeeded | document={doc_id_label} | text_length={len(result['raw_text'])} chars")
                    return result
                else:
                    logger.warning(f"[DocumentAI] Returned empty text for {doc_id_label}. Falling back to Gemini.")
            except Exception as e:
                logger.warning(f"[DocumentAI] Failed for {doc_id_label}: {e}. Falling back to Gemini.")

        # --- Attempt 2: Gemini Vision Fallback (always available) ---
        return await self._extract_with_gemini(file_bytes, mime_type, doc_id_label)

    async def _extract_with_docai(self, file_bytes: bytes, mime_type: str, gcs_path: Optional[str], document_id: Optional[str]) -> Dict[str, Any]:
        """Try Document AI synchronous processing."""
        from google.cloud import documentai

        raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)
        request = documentai.ProcessRequest(
            name=self.processor_name,
            raw_document=raw_document,
        )

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: self.client.process_document(request=request))
        document = result.document

        pages_data = []
        for i, page in enumerate(document.pages):
            page_text = ""
            if hasattr(page, "layout") and hasattr(page.layout, "text_anchor"):
                for segment in page.layout.text_anchor.text_segments:
                    start_index = segment.start_index if segment.start_index else 0
                    end_index = segment.end_index
                    page_text += document.text[start_index:end_index]
            pages_data.append({"page_number": i + 1, "text": page_text})

        return {
            "raw_text": document.text or "",
            "pages": pages_data,
            "page_count": len(document.pages),
            "tables_found": sum(len(page.tables) for page in document.pages),
            "modality": "pdf" if "pdf" in mime_type else "docx",
        }

    async def _extract_with_gemini(self, file_bytes: bytes, mime_type: str, doc_id_label: str) -> Dict[str, Any]:
        """
        Use Gemini Vision to extract text from document bytes.
        Tries multiple models to handle 503 rate limits.
        """
        from google import genai
        from google.genai import types

        client = genai.Client()

        prompt = (
            "Extract ALL text from this document completely and accurately. "
            "Preserve the original structure including headings, paragraphs, tables, and lists. "
            "Output only the extracted text without any commentary or explanation."
        )

        # Build the model list: env-configured model first, then fallbacks
        env_model = os.environ.get("GEMINI_TEXT_MODEL", "gemini-3.5-flash")
        models_to_try = [env_model] + [m for m in GEMINI_FALLBACK_MODELS if m != env_model]

        last_error = None
        
        is_pdf = "pdf" in mime_type.lower()
        pdf_images = []
        if is_pdf:
            try:
                import fitz
                fitz.TOOLS.mupdf_display_errors(False)
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=150)
                    pdf_images.append(pix.tobytes("jpeg"))
                logger.info(f"[GeminiExtractor] Split PDF into {len(pdf_images)} images.")
            except ImportError:
                logger.warning("[GeminiExtractor] pymupdf (fitz) not installed. Falling back to native PDF extraction.")
                is_pdf = False
            except Exception as e:
                logger.warning(f"[GeminiExtractor] Failed to split PDF: {e}. Falling back to native PDF extraction.")
                is_pdf = False

        for model in models_to_try:
            try:
                logger.info(f"[GeminiExtractor] Trying model={model} for document={doc_id_label}")

                loop = asyncio.get_running_loop()

                if is_pdf and pdf_images:
                    pages_data = []
                    full_text = ""
                    for i, img_bytes in enumerate(pdf_images):
                        def _call_page(m=model, img=img_bytes):
                            return client.models.generate_content(
                                model=m,
                                contents=[
                                    types.Part.from_bytes(data=img, mime_type="image/jpeg"),
                                    prompt,
                                ],
                            )
                        response = await loop.run_in_executor(None, _call_page)
                        page_text = response.text or ""
                        pages_data.append({"page_number": i + 1, "text": page_text})
                        full_text += f"\n\n--- Page {i + 1} ---\n\n{page_text}"
                        
                        # Small delay to avoid instantly hitting rate limits
                        await asyncio.sleep(0.5)

                    extracted_text = full_text
                    return {
                        "raw_text": extracted_text,
                        "pages": pages_data,
                        "page_count": len(pdf_images),
                        "tables_found": 1 if "table" in extracted_text.lower() else 0,
                        "modality": "pdf",
                    }
                else:
                    def _call(m=model):
                        return client.models.generate_content(
                            model=m,
                            contents=[
                                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                                prompt,
                            ],
                        )

                    response = await loop.run_in_executor(None, _call)
                    extracted_text = response.text or ""

                    if extracted_text.strip():
                        logger.info(
                            f"[GeminiExtractor] SUCCESS | model={model} | document={doc_id_label} | "
                            f"text_length={len(extracted_text)} chars"
                        )
                        return {
                            "raw_text": extracted_text,
                            "pages": [{"page_number": 1, "text": extracted_text}],
                            "page_count": 1,
                            "tables_found": 1 if "table" in extracted_text.lower() else 0,
                            "modality": "pdf" if "pdf" in mime_type else "docx",
                        }
                    else:
                        logger.warning(f"[GeminiExtractor] Model {model} returned empty text.")

            except Exception as e:
                last_error = e
                error_str = str(e)
                if "503" in error_str or "UNAVAILABLE" in error_str:
                    logger.warning(f"[GeminiExtractor] Model {model} overloaded (503). Trying next model...")
                    continue
                elif "404" in error_str or "NOT_FOUND" in error_str:
                    logger.warning(f"[GeminiExtractor] Model {model} not found (404). Trying next model...")
                    continue
                else:
                    logger.error(f"[GeminiExtractor] Model {model} failed with unexpected error: {e}")
                    continue

        # All models failed
        error_msg = f"All Gemini models failed for document {doc_id_label}. Last error: {last_error}"
        logger.error(f"[GeminiExtractor] {error_msg}")
        raise Exception(error_msg)


document_ai_processor = DocumentAIProcessor()

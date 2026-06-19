import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class VisionOCRProcessor:
    def __init__(self):
        self.mock_mode = False
        self.model = os.getenv("GEMINI_VISION_MODEL", os.getenv("GEMINI_TEXT_MODEL", "gemini-3.5-flash"))
        try:
            from google import genai  # noqa: F401 — validate import at startup
        except Exception as e:
            logger.warning(f"Failed to import google-genai SDK. Running in mock mode: {e}")
            self.mock_mode = True

    async def process_image(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Uses Gemini Vision (google-genai SDK) for image OCR and analysis.
        Passes the image inline as bytes using types.Part.from_bytes().
        """
        if self.mock_mode:
            logger.info(f"[MOCK VISION] Processing {mime_type} image of size {len(file_bytes)} bytes")
            return {
                "raw_text": "This is mocked handwritten text from an image: 'Call John at 5pm'.",
                "modality": "image",
                "image_meta": {
                    "ocr_confidence": 0.95,
                    "contains_handwriting": True,
                },
            }

        try:
            import asyncio
            from google import genai
            from google.genai import types

            client = genai.Client()

            prompt = (
                "Extract all text from this image, preserving structure and layout. "
                "Identify if the text is printed or handwritten."
            )

            # Pass image inline — recommended for files < 20 MB (our limit is 50 MB but images are typically small)
            loop = asyncio.get_running_loop()

            def _call():
                return client.models.generate_content(
                    model=self.model,
                    contents=[
                        types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                        prompt,
                    ],
                )

            response = await loop.run_in_executor(None, _call)
            extracted_text = response.text or ""

            return {
                "raw_text": extracted_text,
                "modality": "image",
                "image_meta": {
                    "ocr_confidence": 0.98,
                    "contains_handwriting": "handwritten" in extracted_text.lower(),
                },
            }
        except Exception as e:
            logger.error(f"Failed to process image with Vision OCR ({self.model}): {e}")
            raise


vision_ocr_processor = VisionOCRProcessor()

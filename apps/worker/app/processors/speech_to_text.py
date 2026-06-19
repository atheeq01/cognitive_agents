import logging
import os
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SpeechToTextProcessor:
    def __init__(self):
        self.mock_mode = False
        self.model = os.getenv("GEMINI_AUDIO_MODEL", os.getenv("GEMINI_TEXT_MODEL", "gemini-3.5-flash"))
        try:
            from google import genai
        except Exception as e:
            logger.warning(f"Failed to import google-genai SDK. Running in mock mode: {e}")
            self.mock_mode = True

    async def process_audio(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Uses Gemini to transcribe audio or video files.
        """
        if self.mock_mode:
            logger.info(f"[MOCK SPEECH] Processing {mime_type} media of size {len(file_bytes)} bytes")
            return {
                "raw_text": "SPEAKER_1: Hello.\nSPEAKER_2: Hi, how are you?",
                "modality": "audio" if mime_type.startswith("audio/") else "video",
                "audio_meta": {
                    "utterances": [
                        {"speaker_id": "SPEAKER_1", "text": "Hello.", "start_time": "0.0s"},
                        {"speaker_id": "SPEAKER_2", "text": "Hi, how are you?", "start_time": "1.5s"}
                    ]
                }
            }

        try:
            from google import genai
            from google.genai import types

            client = genai.Client()
            prompt = (
                "Please transcribe the speech in this media file exactly as spoken. "
                "If there are multiple speakers, label them as Speaker 1, Speaker 2, etc. "
                "and preserve the dialogue structure."
            )

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
                "modality": "audio" if mime_type.startswith("audio/") else "video",
                "audio_meta": {
                    "utterances": []
                }
            }
        except Exception as e:
            logger.error(f"Failed to process media with Gemini: {e}")
            raise

speech_to_text_processor = SpeechToTextProcessor()


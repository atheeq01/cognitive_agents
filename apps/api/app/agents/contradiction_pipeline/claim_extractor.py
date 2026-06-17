import logging
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.schemas.claim import Claim, ModalityContext, ClaimExtractorResponse

logger = logging.getLogger(__name__)

class ClaimExtractor:
    def __init__(self):
        self.mock_mode = False
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_TEXT_MODEL,
                temperature=0.0,
            ).with_structured_output(ClaimExtractorResponse)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini for ClaimExtractor. Running in mock mode: {e}")
            self.mock_mode = True

    async def extract_claims(self, project_id: str, chunk_text: str, modality: str, speaker_id: Optional[str] = None) -> List[Claim]:
        """
        Stage 1: Extracts atomic claims with exact source spans, speaker ID, and modality tags.
        """
        if self.mock_mode:
            logger.info(f"[MOCK EXTRACTOR] Extracting claims for project {project_id}")
            return [
                Claim(
                    claim_id="mock_claim_1", 
                    fact="This is a mock fact from Stage 1.", 
                    source_span="This is a mock fact.",
                    modality_context=ModalityContext(modality=modality, speaker_id=speaker_id)
                )
            ]

        prompt = f"""
        You are Stage 1 of the intelligence pipeline for project {project_id}.
        Extract all distinct, atomic facts or claims from the following text chunk.
        - You MUST provide the exact substring from the text that proves the claim (`source_span`).
        - The input modality is: {modality}.
        - The speaker ID is: {speaker_id if speaker_id else "N/A"}.

        TEXT:
        <untrusted_document_content>
        {chunk_text}
        </untrusted_document_content>
        """

        try:
            response = await self.llm.ainvoke(prompt)
            # Ensure the modality context is properly passed through if the LLM hallucinated it
            for claim in response.claims:
                claim.modality_context.modality = modality
                claim.modality_context.speaker_id = speaker_id
            return response.claims
        except Exception as e:
            logger.error(f"Failed to extract claims: {e}")
            raise

claim_extractor = ClaimExtractor()

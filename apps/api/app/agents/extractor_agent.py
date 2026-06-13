import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class Claim(BaseModel):
    claim_id: str = Field(description="A unique ID for this claim")
    fact: str = Field(description="The atomic statement or fact extracted from the text")
    source_span: str = Field(description="The exact quote from the text that proves this claim")
    speaker_id: Optional[str] = Field(None, description="The person who stated this claim, if applicable")

class ExtractorResponse(BaseModel):
    claims: List[Claim]

class ExtractorAgent:
    def __init__(self):
        # We assume GEMINI_API_KEY is in the environment for the LLM to pick up automatically
        # For local testing, we fallback to a mock response if initialization fails
        self.mock_mode = False
        try:
            # We use gemini-1.5-flash as it's the fastest and most efficient for structured extraction
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.0,
            ).with_structured_output(ExtractorResponse)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini. Running ExtractorAgent in mock mode: {e}")
            self.mock_mode = True

    async def extract_claims(self, project_id: str, chunk_text: str) -> List[Claim]:
        """
        Takes a raw chunk of text and uses Gemini to extract atomic claims with their source spans.
        """
        if self.mock_mode:
            logger.info(f"[MOCK EXTRACTOR] Extracting claims for project {project_id}")
            return [
                Claim(
                    claim_id="mock_claim_1", 
                    fact="This is a mock fact.", 
                    source_span="This is a mock fact."
                )
            ]

        prompt = f"""
        You are a highly analytical extractor agent serving project {project_id}.
        Your job is to read the following text chunk and extract all distinct, atomic claims, facts, or statements.
        For each claim, you MUST provide the exact substring from the text that proves the claim.
        Do not hallucinate. Do not infer. Only extract what is explicitly stated.

        TEXT:
        {chunk_text}
        """

        try:
            response = await self.llm.ainvoke(prompt)
            return response.claims
        except Exception as e:
            logger.error(f"Failed to extract claims: {e}")
            raise

extractor_agent = ExtractorAgent()

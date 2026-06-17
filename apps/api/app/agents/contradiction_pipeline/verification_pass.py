import logging
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class VerificationResult(BaseModel):
    is_contradiction: bool = Field(description="True if the two quotes definitively contradict each other")
    reasoning: str = Field(description="A one-sentence explanation of why they contradict or why they don't")

class VerificationPass:
    def __init__(self):
        self.mock_mode = False
        try:
            # We use a fresh LLM instance to ensure completely clean context
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_TEXT_MODEL,
                temperature=0.0,
            ).with_structured_output(VerificationResult)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini for VerificationPass. Running in mock mode: {e}")
            self.mock_mode = True

    async def verify_conflict(self, evidence_a: str, evidence_b: str) -> VerificationResult:
        """
        Stage 4: Clean-room verification pass.
        The LLM receives ONLY the two evidence quotes to prevent context hallucination.
        """
        if self.mock_mode:
            logger.info(f"[MOCK VERIFIER] Verifying conflict")
            return VerificationResult(is_contradiction=True, reasoning="Mock verification passed.")

        prompt = f"""
        You are an independent auditor. Your only job is to evaluate whether Quote A and Quote B represent a factual or logical contradiction.
        Do not assume any outside context. Evaluate strictly on the text provided.

        QUOTE A:
        "{evidence_a}"

        QUOTE B:
        "{evidence_b}"

        Do they definitively contradict each other?
        """

        try:
            return await self.llm.ainvoke(prompt)
        except Exception as e:
            logger.error(f"Failed to verify conflict: {e}")
            raise

verifier_agent = VerificationPass()

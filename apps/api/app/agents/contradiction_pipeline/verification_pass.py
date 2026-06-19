import logging
import time
from pydantic import BaseModel, Field
from app.agents.pipeline import BaseAgent

logger = logging.getLogger(__name__)

class VerificationResult(BaseModel):
    is_contradiction: bool = Field(description="True if the two quotes definitively contradict each other")
    reasoning: str = Field(description="A one-sentence explanation of why they contradict or why they don't")

class VerificationPass(BaseAgent):
    def __init__(self):
        super().__init__("VerificationPass")
        self.mock_mode = False

    async def verify_conflict(self, evidence_a: str, evidence_b: str) -> VerificationResult:
        """
        Stage 4: Clean-room verification pass.
        The LLM receives ONLY the two evidence quotes to prevent context hallucination.
        """
        if self.mock_mode:
            logger.info("[MOCK VERIFIER] Verifying conflict")
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

        response = await self._execute_with_fallback(
            prompt=prompt,
            project_id="verification_pass", # The base class expects a project ID for logging
            structured_output_type=VerificationResult,
            temperature=0.0,
            timeout=20.0,
            llm_timeout=15,
        )

        if response is not None:
            return response

        return VerificationResult(is_contradiction=False, reasoning="Failed to verify conflict due to AI service unavailability.")

verifier_agent = VerificationPass()

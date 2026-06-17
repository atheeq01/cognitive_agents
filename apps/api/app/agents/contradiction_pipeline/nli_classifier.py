import logging
from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class NLIResult(BaseModel):
    relation: Literal["ENTAILMENT", "NEUTRAL", "CONTRADICTION"] = Field(
        description="The logical relationship between Claim A and Claim B"
    )
    conflict_type: Optional[Literal["factual", "temporal", "definitional", "logical", "cross-modal"]] = Field(
        None, description="If a contradiction, what type of conflict is it?"
    )
    evidence_a: Optional[str] = Field(
        None, description="The exact quote from Claim A that supports the contradiction. REQUIRED if CONTRADICTION."
    )
    evidence_b: Optional[str] = Field(
        None, description="The exact quote from Claim B that supports the contradiction. REQUIRED if CONTRADICTION."
    )

class NLIClassifier:
    def __init__(self):
        self.mock_mode = False
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_TEXT_MODEL,
                temperature=0.0,
            ).with_structured_output(NLIResult)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini for NLIClassifier. Running in mock mode: {e}")
            self.mock_mode = True

    async def classify_pair(self, claim_a: dict, claim_b: dict) -> NLIResult:
        """
        Stage 3: Cross-modal Natural Language Inference.
        Evaluates two claims and determines if they entail each other, are neutral, or contradict.
        """
        if self.mock_mode:
            logger.info(f"[MOCK NLI] Classifying pair")
            return NLIResult(
                relation="CONTRADICTION",
                conflict_type="factual",
                evidence_a="Claim A says X",
                evidence_b="Claim B says Y"
            )

        # Build context aware prompt
        prompt = f"""
        You are Stage 3 of an intelligence pipeline evaluating cross-modal claims.
        Determine the logical relationship between Claim A and Claim B.

        CLAIM A CONTEXT:
        Modality: {claim_a.get('modality', 'unknown')}
        Speaker: {claim_a.get('speaker_id', 'N/A')}
        Statement: {claim_a.get('fact', '')}
        Source Quote: {claim_a.get('source_span', '')}

        CLAIM B CONTEXT:
        Modality: {claim_b.get('metadata', {}).get('modality', 'unknown')}
        Speaker: {claim_b.get('metadata', {}).get('speaker_id', 'N/A')}
        Statement: {claim_b.get('metadata', {}).get('fact', '')}
        Source Quote: {claim_b.get('metadata', {}).get('source_span', '')}

        INSTRUCTIONS:
        1. Classify the relationship as ENTAILMENT, NEUTRAL, or CONTRADICTION.
        2. If CONTRADICTION, you MUST provide the exact `evidence_a` and `evidence_b` quotes from the Source Quotes above.
        3. Note: Two different speakers can have opposing views legitimately. If Speaker A disagrees with Speaker B, that is still a CONTRADICTION that must be flagged.
        """

        try:
            result = await self.llm.ainvoke(prompt)
            # Hard validation
            if result.relation == "CONTRADICTION" and (not result.evidence_a or not result.evidence_b):
                logger.error("LLM failed to provide evidence for CONTRADICTION")
                result.relation = "NEUTRAL" # Fail safe
            return result
        except Exception as e:
            logger.error(f"Failed to classify NLI: {e}")
            raise

nli_classifier = NLIClassifier()

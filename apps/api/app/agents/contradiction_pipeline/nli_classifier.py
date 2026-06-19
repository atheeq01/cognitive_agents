import logging
import time
from typing import Literal, Optional
from pydantic import BaseModel, Field
from app.agents.pipeline import BaseAgent

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

class NLIClassifier(BaseAgent):
    def __init__(self):
        super().__init__("NLIClassifier")
        self.mock_mode = False

    async def classify_pair(self, claim_a: dict | str, claim_b: dict | str) -> NLIResult:
        """
        Stage 3: Cross-modal Natural Language Inference.
        Evaluates two claims and determines if they entail each other, are neutral, or contradict.
        """
        if self.mock_mode:
            logger.info("[MOCK NLI] Classifying pair")
            return NLIResult(
                relation="CONTRADICTION",
                conflict_type="factual",
                evidence_a="Claim A says X",
                evidence_b="Claim B says Y"
            )

        # Handle both string and dict inputs
        def _extract_context(c):
            if isinstance(c, str):
                return {"modality": "unknown", "speaker_id": "N/A", "fact": c, "source_span": ""}
            
            fact = c.get("fact", c.get("text", ""))
            
            loc = c.get("source_location", {})
            if isinstance(loc, str):
                import json
                try:
                    loc = json.loads(loc)
                except:
                    loc = {}
                    
            modality = loc.get("modality", "unknown") if isinstance(loc, dict) else "unknown"
            speaker_id = loc.get("speaker_id", "N/A") if isinstance(loc, dict) else "N/A"
            source_span = loc.get("exact_quote", "") if isinstance(loc, dict) else ""
            
            return {
                "modality": modality,
                "speaker_id": speaker_id,
                "fact": fact,
                "source_span": source_span
            }

        ctx_a = _extract_context(claim_a)
        ctx_b = _extract_context(claim_b)

        # Build context aware prompt
        prompt = f"""
        You are Stage 3 of an intelligence pipeline evaluating cross-modal claims.
        Determine the logical relationship between Claim A and Claim B.

        CLAIM A CONTEXT:
        Modality: {ctx_a['modality']}
        Speaker: {ctx_a['speaker_id']}
        Statement: {ctx_a['fact']}
        Source Quote: {ctx_a['source_span']}

        CLAIM B CONTEXT:
        Modality: {ctx_b['modality']}
        Speaker: {ctx_b['speaker_id']}
        Statement: {ctx_b['fact']}
        Source Quote: {ctx_b['source_span']}

        INSTRUCTIONS:
        1. Classify the relationship as ENTAILMENT, NEUTRAL, or CONTRADICTION.
        2. If CONTRADICTION, you MUST provide the exact `evidence_a` and `evidence_b` quotes from the Source Quotes above. If source quotes are empty, use the Statement.
        3. Note: Two different speakers can have opposing views legitimately. If Speaker A disagrees with Speaker B, that is still a CONTRADICTION that must be flagged.
        """

        result = await self._execute_with_fallback(
            prompt=prompt,
            project_id="nli_classifier",
            structured_output_type=NLIResult,
            temperature=0.0,
            timeout=20.0,
            llm_timeout=15,
        )

        if result is not None:
            # Hard validation
            if result.relation == "CONTRADICTION" and (not result.evidence_a or not result.evidence_b):
                logger.error("LLM failed to provide evidence for CONTRADICTION")
                result.relation = "NEUTRAL" # Fail safe
            return result

        return NLIResult(relation="NEUTRAL")

nli_classifier = NLIClassifier()

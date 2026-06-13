import logging
from typing import Literal

logger = logging.getLogger(__name__)

class SeverityScorer:
    def score_conflict(self, claim_a: dict, claim_b: dict, conflict_type: str) -> Literal["CRITICAL", "HIGH", "LOW"]:
        """
        Stage 5: Calculates severity based on modality rules, temporal ordering, and document authority.
        """
        modality_a = claim_a.get("modality", "unknown")
        modality_b = claim_b.get("metadata", {}).get("modality", "unknown")
        
        # 1. Cross-modal conflicts (especially involving signed docs like pdfs) get elevated automatically
        if modality_a != modality_b:
            if "pdf" in [modality_a, modality_b] or "docx" in [modality_a, modality_b]:
                return "CRITICAL"
                
        # 2. Hard factual conflicts or temporal sequence conflicts
        if conflict_type in ["factual", "temporal"]:
            return "HIGH"
            
        # 3. Default fallback for stylistic, definitional, or minor logical disagreements
        return "LOW"

severity_scorer = SeverityScorer()

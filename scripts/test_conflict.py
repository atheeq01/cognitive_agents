import asyncio
import logging
from app.agents.contradiction_pipeline import (
    claim_extractor,
    candidate_selector,
    nli_classifier,
    verifier_agent,
    severity_scorer
)
from app.firestore.conflicts_store import conflicts_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pipeline():
    project_id = "test-project-123"
    chunk_text = "The Acme corp deal was finalized strictly on March 15th."
    modality = "audio"
    speaker_id = "Speaker 1"
    
    logger.info("=== STAGE 1: Claim Extraction ===")
    claims = await claim_extractor.extract_claims(project_id, chunk_text, modality, speaker_id)
    new_claim = claims[0]
    logger.info(f"Extracted: {new_claim.fact}")
    
    logger.info("\n=== STAGE 2: Candidate Selection ===")
    # We pass a dict representation to the NLI step for ease, so let's format it
    claim_dict = {
        "fact": new_claim.fact,
        "source_span": new_claim.source_span,
        "modality": new_claim.modality_context.modality,
        "speaker_id": new_claim.modality_context.speaker_id
    }
    candidates = await candidate_selector.select_candidates(project_id, new_claim.fact)
    
    if not candidates:
        logger.info("No candidates found.")
        return
        
    candidate = candidates[0]
    logger.info(f"Found highly similar claim from Pinecone with score: {candidate['score']}")
    
    logger.info("\n=== STAGE 3: NLI Classifier ===")
    nli_result = await nli_classifier.classify_pair(claim_dict, candidate)
    logger.info(f"NLI Classification: {nli_result.relation} ({nli_result.conflict_type})")
    
    if nli_result.relation == "CONTRADICTION":
        logger.info("\n=== STAGE 4: Verification Pass ===")
        verif_result = await verifier_agent.verify_conflict(nli_result.evidence_a, nli_result.evidence_b)
        logger.info(f"Verifier agrees? {verif_result.is_contradiction} ({verif_result.reasoning})")
        
        if verif_result.is_contradiction:
            logger.info("\n=== STAGE 5: Severity Scoring & Firestore Queue ===")
            severity = severity_scorer.score_conflict(claim_dict, candidate, nli_result.conflict_type)
            logger.info(f"Severity calculated: {severity}")
            
            conflict_data = {
                "severity": severity,
                "conflict_type": nli_result.conflict_type,
                "evidence_a": nli_result.evidence_a,
                "evidence_b": nli_result.evidence_b,
                "modality_a": claim_dict["modality"],
                "modality_b": candidate["metadata"].get("modality", "unknown")
            }
            
            conflict_id = conflicts_store.route_to_human_review(project_id, conflict_data)
            logger.info(f"Final conflict written to Firestore Queue: {conflict_id}")

if __name__ == "__main__":
    asyncio.run(run_pipeline())

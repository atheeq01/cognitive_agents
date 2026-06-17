import asyncio
import logging
from typing import Dict, Any, List

from app.agents.extractor_agent import extractor_agent
from app.agents.summarizer_agent import summarizer_agent
from app.agents.cognitive_agent import cognitive_agent
from app.agents.similarity_agent import similarity_agent
from app.agents.contradiction_pipeline.candidate_selector import candidate_selector
from app.agents.contradiction_pipeline.verification_pass import verifier_agent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    async def process_chunk(self, project_id: str, chunk_text: str) -> Dict[str, Any]:
        """
        Orchestrates the parallel execution of intelligence agents on a single chunk of text.
        """
        logger.info(f"Orchestrator starting parallel processing for project {project_id}")
        try:
            claims_task = asyncio.create_task(extractor_agent.extract_claims(project_id, chunk_text))
            summary_task = asyncio.create_task(summarizer_agent.summarize_chunk(project_id, chunk_text))
            
            claims, summary = await asyncio.gather(claims_task, summary_task)
            
            return {
                "summary": summary,
                "claims": [claim.model_dump() for claim in claims]
            }
        except Exception as e:
            logger.error(f"Orchestrator failed during processing: {e}")
            raise

    async def process_full_document(self, project_id: str, raw_text: str) -> Dict[str, Any]:
        """
        Runs document-level agents (like Cognitive Analysis).
        """
        try:
            cognitive_insights = await cognitive_agent.analyze_document(project_id, raw_text)
            return {
                "cognitive_insights": cognitive_insights
            }
        except Exception as e:
            logger.error(f"Failed to process full document: {e}")
            raise
            
    async def run_cross_document_analysis(self, project_id: str, document_id: str, document_summary: str, all_claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes Phase 2: Compares the new document against previous documents in the Vector DB.
        """
        logger.info(f"Starting cross-document analysis for {document_id}")
        
        # 1. Similarity
        similarities = await similarity_agent.evaluate_similarity(project_id, document_id, document_summary)
        
        # 2. Contradictions (Globalized)
        contradictions = []
        for claim in all_claims:
            claim_text = claim.get('fact', '')
            if not claim_text:
                continue
                
            candidates = await candidate_selector.select_candidates(project_id, claim_text)
            for cand in candidates:
                # Assuming candidate selector returned candidates from other documents
                cand_doc_id = cand['metadata'].get('document_id') if cand['metadata'] else None
                if cand_doc_id == document_id:
                    continue # Skip claims from the same document
                    
                cand_fact = cand['metadata'].get('fact', '')
                if not cand_fact:
                    continue
                    
                result = await verifier_agent.verify_conflict(evidence_a=claim_text, evidence_b=cand_fact)
                if result.is_contradiction:
                    contradictions.append({
                        "conflicting_document_id": cand_doc_id,
                        "quote_a": claim_text,
                        "quote_b": cand_fact,
                        "reasoning": result.reasoning
                    })
                    
        return {
            "similarities": similarities,
            "contradictions": contradictions
        }

orchestrator = AgentOrchestrator()

import logging
import json
from typing import List, Dict, Any
from app.agents.pipeline import BaseAgent

logger = logging.getLogger(__name__)

class ProjectSynthesisAgent(BaseAgent):
    """
    Runs AFTER any document in a project finishes processing.
    Pulls every completed document in the project and produces ONE
    unified, human-readable project report.
    """
    def __init__(self):
        super().__init__("ProjectSynthesisAgent")
        self.mock_mode = False

    def _build_candidate_pairs(self, all_claims: List[Dict[str, Any]], score_threshold: float = 0.80) -> List[tuple]:
        """
        Since we already have all claims, we can either do an O(N^2) comparison in-memory 
        if we embedded them, or we can use Pinecone to find similar claims. 
        Because we're keeping it simple and all_claims might be large, 
        we will simulate clustering by finding claims from DIFFERENT documents.
        To avoid massive O(N^2) LLM calls, we can randomly sample or pair them.
        But ideally, we should query Pinecone for each claim to find its nearest neighbors.
        """
        # A true clustering would happen here. For now, we will pair claims across different documents.
        # To avoid O(N^2), we'll do a naive pairing of claims from doc A with doc B.
        pairs = []
        # In a real production system, you'd do an HNSW or agglomerative clustering here.
        # Since we just want the pipeline to work, we'll do a bounded cross-product.
        # To make it efficient, we only pair up to 10 claims per document with others.
        for i, claim_a in enumerate(all_claims):
            for j, claim_b in enumerate(all_claims[i+1:]):
                doc_a = claim_a.get("document_id")
                doc_b = claim_b.get("document_id")
                if doc_a and doc_b and doc_a != doc_b:
                    pairs.append((claim_a, claim_b))
                    if len(pairs) > 20: # Cap to avoid burning API limits in demo
                        return pairs
        return pairs

    async def synthesize(self, project_id: str, docs: List[Dict[str, Any]], all_claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        from datetime import datetime, timezone
        from app.schemas.report import ProjectReport
        
        if len(docs) < 1:
            return None

        logger.info(f"[{self.agent_name}] Synthesizing project {project_id} | docs={len(docs)} claims={len(all_claims)}")

        # Fix stringified source_locations from Pinecone
        for claim in all_claims:
            if "source_location" in claim and isinstance(claim["source_location"], str) and claim["source_location"]:
                try:
                    claim["source_location"] = json.loads(claim["source_location"])
                except Exception:
                    pass

        candidate_pairs = self._build_candidate_pairs(all_claims)
        raw_contradictions = []
        raw_agreements = []
        
        logger.info(f"[{self.agent_name}] Evaluating {len(candidate_pairs)} candidate claim pairs.")
        
        for d in docs:
            results = d.get("results", {})
            contras = results.get("contradictions", [])
            sims = results.get("similarities", [])
            
            for c in contras:
                raw_contradictions.append({
                    "claim_a": {
                        "fact": c.get("quote_a"),
                        "source_location": c.get("source_location", {})
                    },
                    "claim_b": {
                        "fact": c.get("quote_b"),
                        "source_location": c.get("target_source_location", {})
                    },
                    "conflict_type": c.get("conflict_type"),
                    "reasoning": c.get("reasoning")
                })
            
            for s in sims:
                raw_agreements.append({
                    "claim_a": {
                        "fact": s.get("source_claim"),
                        "source_location": s.get("source_location", {})
                    },
                    "claim_b": {
                        "fact": s.get("target_claim"),
                        "source_location": s.get("target_source_location", {})
                    }
                })

        from app.agents.contradiction_pipeline.nli_classifier import nli_classifier
        from app.agents.contradiction_pipeline.verification_pass import verifier_agent

        for claim_a, claim_b in candidate_pairs:
            fact_a = claim_a.get("fact", "")
            fact_b = claim_b.get("fact", "")
            if not fact_a or not fact_b:
                continue
            try:
                nli = await nli_classifier.classify_pair(claim_a, claim_b)
                if nli.relation == "CONTRADICTION":
                    verified = await verifier_agent.verify_conflict(nli.evidence_a, nli.evidence_b)
                    if verified.is_contradiction:
                        raw_contradictions.append({
                            "claim_a": claim_a,
                            "claim_b": claim_b,
                            "conflict_type": nli.conflict_type,
                            "reasoning": verified.reasoning
                        })
                elif nli.relation == "ENTAILMENT":
                    raw_agreements.append({
                        "claim_a": claim_a,
                        "claim_b": claim_b
                    })
            except Exception as e:
                logger.error(f"[{self.agent_name}] Error comparing claims: {e}")
                
        logger.info(f"[{self.agent_name}] Found {len(raw_contradictions)} raw contradictions and {len(raw_agreements)} raw agreements.")
        
        report = await self._generate_project_report(project_id, docs, raw_contradictions, raw_agreements)
        return report

    async def _generate_project_report(self, project_id: str, docs: List[Dict[str, Any]], raw_contradictions: list, raw_agreements: list) -> Dict[str, Any]:
        from datetime import datetime, timezone
        from app.schemas.report import ProjectReport, ContradictionFinding, AgreementFinding, CognitiveInsights, SourceLocation
        
        if self.mock_mode:
            logger.warning(f"[{self.agent_name}] Running in mock mode, returning dummy report.")
            return ProjectReport(
                project_id=project_id,
                document_count=len(docs),
                modalities_included=["pdf"],
                unified_summary="Mock unified summary.",
                cognitive_synthesis=CognitiveInsights(),
                contradictions=[],
                agreements=[],
                generated_at=datetime.now(timezone.utc)
            ).model_dump()

        doc_summaries = [
            {"document_name": d.get("documentName", d.get("document_name", "Unknown")), "summary": d.get("results", {}).get("summary", "No summary")} 
            for d in docs
        ]
        doc_insights = [
            {"document_name": d.get("documentName", d.get("document_name", "Unknown")), "insights": d.get("results", {}).get("cognitive_insights", {})} 
            for d in docs
        ]
        
        # We need a schema without datetime for LLM generation
        from pydantic import BaseModel
        class ProjectReportGeneration(BaseModel):
            unified_summary: str
            cognitive_synthesis: CognitiveInsights
            contradictions: List[ContradictionFinding]
            agreements: List[AgreementFinding]

        prompt = f"""
You are the Project Synthesis Agent. Your task is to analyze documents in a project and generate a structured intelligence report.
Number of documents: {len(docs)}

We have run pair-wise claim comparison and found these RAW CONTRADICTIONS and RAW AGREEMENTS.
Your task is to deduplicate and cluster these: if claims from 3+ documents collide on the same topic, merge them into one ContradictionFinding/AgreementFinding.
Also, synthesize the document summaries and cognitive insights into one unified, project-wide narrative.

IMPORTANT INSTRUCTIONS FOR THE UNIFIED SUMMARY & COGNITIVE SYNTHESIS:
The user needs to know exactly where the information in the Unified Summary and Cognitive Synthesis comes from. 
Whenever you mention a fact, insight, or summary detail, you MUST include an inline citation formatted as `[Source: document_name, p.X]`. Do NOT write vague statements. Every significant point must have a citation linking it back to the specific document name and page number.

RAW CONTRADICTIONS:
{json.dumps(raw_contradictions, default=str)}

RAW AGREEMENTS:
{json.dumps(raw_agreements, default=str)}

DOCUMENT SUMMARIES:
{json.dumps(doc_summaries, default=str)}

DOCUMENT COGNITIVE INSIGHTS:
{json.dumps(doc_insights, default=str)}

IMPORTANT: For the `source_location` fields in ContradictionFinding and AgreementFinding, you MUST copy the exact JSON object provided in the raw data under `claim_a.source_location` or `claim_b.source_location`. Do not invent source locations.
"""
        
        response = await self._execute_with_fallback(
            prompt=prompt,
            project_id=project_id,
            structured_output_type=ProjectReportGeneration,
            temperature=0.3,
            timeout=120.0,
            llm_timeout=30,
        )
        
        if not response:
            logger.error(f"[{self.agent_name}] All models failed to generate report")
            # Fallback bare report
            return ProjectReport(
                project_id=project_id,
                document_count=len(docs),
                modalities_included=["unknown"],
                unified_summary="Failed to generate unified summary due to API error.",
                cognitive_synthesis=CognitiveInsights(),
                contradictions=[],
                agreements=[],
                generated_at=datetime.now(timezone.utc)
            ).model_dump()
            
        try:
            modalities = set()
            for doc in docs:
                m = doc.get("results", {}).get("modality") or doc.get("modality")
                if m:
                    modalities.add(m)
            if not modalities:
                modalities = {"pdf"} # Default
                
            report = ProjectReport(
                project_id=project_id,
                document_count=len(docs),
                modalities_included=list(modalities),
                unified_summary=response.unified_summary,
                cognitive_synthesis=response.cognitive_synthesis,
                contradictions=response.contradictions,
                agreements=response.agreements,
                generated_at=datetime.now(timezone.utc)
            )
            return report.model_dump()
        except Exception as e:
            logger.error(f"[{self.agent_name}] LLM failed to write project report: {e}")
            # Fallback bare report
            return ProjectReport(
                project_id=project_id,
                document_count=len(docs),
                modalities_included=["unknown"],
                unified_summary="Failed to generate unified summary due to API error.",
                cognitive_synthesis=CognitiveInsights(),
                contradictions=[],
                agreements=[],
                generated_at=datetime.now(timezone.utc)
            ).model_dump()

project_synthesis_agent = ProjectSynthesisAgent()

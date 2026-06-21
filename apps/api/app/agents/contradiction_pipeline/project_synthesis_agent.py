import logging
import json
from typing import List, Dict, Any, Optional
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



    async def synthesize(self, project_id: str, docs: List[Dict[str, Any]], all_claims: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        
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

        raw_contradictions = []
        raw_agreements = []
        
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

        logger.info(f"[{self.agent_name}] Found {len(raw_contradictions)} raw contradictions and {len(raw_agreements)} raw agreements from processed documents.")
        
        report = await self._generate_project_report(project_id, docs, raw_contradictions, raw_agreements, all_claims)
        return report

    async def _generate_project_report(self, project_id: str, docs: List[Dict[str, Any]], raw_contradictions: list, raw_agreements: list, all_claims: list) -> Dict[str, Any]:
        from datetime import datetime, timezone
        from app.schemas.report import ProjectReport, ContradictionFinding, AgreementFinding, CognitiveInsights
        
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

        all_claims_json = json.dumps([{"fact": c.get("fact"), "source_location": c.get("source_location")} for c in all_claims], default=str)
        raw_contradictions_json = json.dumps(raw_contradictions, default=str)
        raw_agreements_json = json.dumps(raw_agreements, default=str)
        doc_summaries_json = json.dumps(doc_summaries, default=str)

        prompt = f"""
You are the Project Synthesis Agent. Your task is to analyze documents in a project and generate a structured intelligence report.
Number of documents: {len(docs)}

We have collected ALL EXTRACTED CLAIMS from every document in this project.
We have also run some automated pair-wise claim comparison to find RAW CONTRADICTIONS and RAW AGREEMENTS, but these may be incomplete.
Your task is to carefully review ALL EXTRACTED CLAIMS, alongside the raw findings, to identify all significant Contradictions and Agreements across the documents.
You must synthesize the document summaries and cognitive insights into one unified, project-wide narrative.

IMPORTANT INSTRUCTIONS FOR THE UNIFIED SUMMARY & COGNITIVE SYNTHESIS:
The user needs to know exactly where the information in the Unified Summary and Cognitive Synthesis comes from. 
Whenever you mention a fact, insight, or summary detail, you MUST include an inline citation formatted as `[Source: document_name, p.X]`. Do NOT write vague statements. Every significant point must have a citation linking it back to the specific document name and page number.

CRITICAL INSTRUCTION FOR AGREEMENTS AND CONTRADICTIONS:
An "Agreement" or "Contradiction" by definition means comparing across MULTIPLE DIFFERENT documents.
When you output an `AgreementFinding` or `ContradictionFinding`, you MUST compare each PDF against the other PDFs. Do not just rely on the raw findings. Use the ALL EXTRACTED CLAIMS list to find deep, cross-document connections and conflicts IF AND ONLY IF they exist.
IMPORTANT: If the documents cover completely unrelated topics, you MUST return empty lists for `contradictions` and `agreements`. DO NOT force or hallucinate conflicts or agreements between unrelated facts.
For Agreements: You MUST include the exact claims from ALL the different documents that form the agreement. `supporting_claims` MUST be a list of at least 2 items (e.g., Claim from Document A, Claim from Document B). `supporting_sources` MUST be a list of at least 2 items, corresponding exactly to the claims. NEVER output an agreement with only 1 claim and 1 source. This is considered unethical and incorrect.
For Contradictions: You MUST include the exact claims from the two opposing documents in `claim_a` and `claim_b`.

ALL EXTRACTED CLAIMS:
{all_claims_json}

RAW CONTRADICTIONS (Use as hints):
{raw_contradictions_json}

RAW AGREEMENTS (Use as hints):
{raw_agreements_json}

DOCUMENT SUMMARIES:
{doc_summaries_json}

DOCUMENT COGNITIVE INSIGHTS:
{json.dumps(doc_insights, default=str)}

IMPORTANT: For the `source_location` fields in ContradictionFinding and AgreementFinding, you MUST copy the exact JSON object provided in the raw data or ALL EXTRACTED CLAIMS. Do not invent source locations.
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

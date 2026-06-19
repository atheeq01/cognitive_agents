import logging
import time
import asyncio
from typing import Type, Any, Optional, List, Dict
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from google.api_core import exceptions as google_exceptions

from app.core.config import settings
from app.schemas.cognitive import CognitiveInsights
from app.schemas.claim import Claim, ClaimExtractorResponse
from app.schemas.similarity import SimilarityMatch, SimilarityReport
from app.vector_store.pinecone_adapter import pinecone_adapter

logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Base class for cognitive agents.
    Provides centralized LLM building, fallback models, and a circuit-breaker retry loop.
    """
    _FALLBACK_MODELS = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    ]

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.primary_model = getattr(settings, "GEMINI_TEXT_MODEL", "gemini-3.5-flash")
        self.models_to_try = [self.primary_model] + [
            m for m in self._FALLBACK_MODELS if m != self.primary_model
        ]
        self._failing_models = {}

    @staticmethod
    def _build_llm(model: str, structured_output_type: Optional[Type[BaseModel]] = None, temperature: float = 0.0, timeout: int = 30):
        llm = ChatGoogleGenerativeAI(model=model, temperature=temperature, max_retries=0, timeout=timeout)
        if structured_output_type:
            return llm.with_structured_output(structured_output_type)
        return llm

    async def _execute_with_fallback(self, prompt: Any, project_id: str, structured_output_type: Optional[Type[BaseModel]] = None, temperature: float = 0.0, timeout: float = 35.0, llm_timeout: int = 30) -> Any:
        last_error = None

        for model in self.models_to_try:
            if time.time() < self._failing_models.get(model, 0):
                continue
            try:
                llm = self._build_llm(model, structured_output_type, temperature, llm_timeout)
                response = await asyncio.wait_for(llm.ainvoke(prompt), timeout=timeout)
                return response
            except asyncio.TimeoutError:
                self._failing_models[model] = time.time() + 60
                continue
            except google_exceptions.ServiceUnavailable:
                self._failing_models[model] = time.time() + 60
                continue
            except google_exceptions.NotFound:
                self._failing_models[model] = time.time() + 300
                continue
            except Exception as e:
                last_error = e
                error_str = str(e)
                if any(err in error_str for err in ["503", "UNAVAILABLE", "504", "DEADLINE_EXCEEDED"]):
                    self._failing_models[model] = time.time() + 60
                    continue
                elif "404" in error_str or "NOT_FOUND" in error_str:
                    self._failing_models[model] = time.time() + 300
                    continue
                else:
                    logger.error(f"[{self.agent_name}] Model {model} failed | error={e}")
                    continue

        logger.error(f"[{self.agent_name}] All models failed for project={project_id} | last_error={last_error}")
        return None

class SummaryResponse(BaseModel):
    summary: str = Field(description="A concise summary of the text chunk")

class EntityLink(BaseModel):
    source_entity_id: str = Field(description="The ID of the source entity")
    target_entity_id: str = Field(description="The ID of the target entity")
    relationship: str = Field(description="A description of the relationship")
    score: float = Field(description="The strength score of the relationship")
    valid_from: Optional[str] = Field(None, description="Start date of relationship if temporal")
    valid_to: Optional[str] = Field(None, description="End date of relationship if temporal")

class ConnectorAgentResponse(BaseModel):
    links: List[EntityLink]

class AgentPipeline(BaseAgent):
    """
    Unified pipeline containing all agent stages.
    """
    def __init__(self):
        super().__init__("AgentPipeline")
        self.mock_mode = False
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(model=settings.GEMINI_EMBEDDING_MODEL)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini embeddings. Mock mode enabled: {e}")
            self.mock_mode = True

    # STAGE 1: Summarization
    async def stage_summarize_chunk(self, project_id: str, chunk_text: str) -> str:
        prompt = f"""
        You are a highly capable summarizer agent serving project {project_id}.
        Your job is to read the following text chunk and provide a clear, concise summary of the main points.
        Do not include external information.

        TEXT:
        {chunk_text}
        """
        response = await self._execute_with_fallback(prompt, project_id, SummaryResponse, 0.2, 20.0, 15)
        return response.summary if response else ""

    # STAGE 2: Claim Extraction
    async def stage_extract_claims(self, project_id: str, chunk_text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Claim]:
        metadata_str = ""
        if metadata:
            lines = ["Known Source Context:"]
            if metadata.get('document_id') is not None: lines.append(f"- Document ID: {metadata['document_id']}")
            if metadata.get('document_name') is not None: lines.append(f"- Document Name: {metadata['document_name']}")
            if metadata.get('modality') is not None: lines.append(f"- Modality: {metadata['modality']}")
            if metadata.get('page_number') is not None: lines.append(f"- Page Number: {metadata['page_number']}")
            if metadata.get('timestamp_start_seconds') is not None: lines.append(f"- Timestamp Start: {metadata['timestamp_start_seconds']}")
            if metadata.get('speaker_id') is not None: lines.append(f"- Speaker ID: {metadata['speaker_id']}")
            metadata_str = "\n            ".join(lines)
        prompt = f"""
        You are a highly analytical extractor agent serving project {project_id}.
        Your job is to read the following text chunk and extract all distinct, atomic claims, facts, or statements.
        For each claim, you MUST provide the `source_location`. Specifically:
        - `exact_quote`: The exact substring from the text that proves the claim.
        - Copy the Known Source Context exactly into the corresponding fields of `source_location` (document_id, document_name, modality, page_number).
        
        {metadata_str}

        Do not hallucinate. Do not infer. Only extract what is explicitly stated.

        TEXT:
        {chunk_text}
        """
        response = await self._execute_with_fallback(prompt, project_id, ClaimExtractorResponse, 0.0, 20.0, 15)
        if response:
            if metadata:
                for claim in response.claims:
                    if claim.source_location:
                        claim.source_location.document_id = metadata.get("document_id", "Unknown")
                        claim.source_location.document_name = metadata.get("document_name", "Unknown")
                        claim.source_location.modality = metadata.get("modality", "Unknown")
                        if metadata.get("page_number") is not None:
                            claim.source_location.page_number = metadata.get("page_number")
                        if metadata.get("timestamp_start_seconds") is not None:
                            claim.source_location.timestamp_start_seconds = metadata.get("timestamp_start_seconds")
                        if metadata.get("speaker_id") is not None:
                            claim.source_location.speaker_id = metadata.get("speaker_id")
            return response.claims
        return []

    # STAGE 3: Cognitive Analysis
    async def stage_cognitive_analysis(self, project_id: str, document_text: str) -> CognitiveInsights:
        prompt = f"""
        You are a deep cognitive analysis agent serving project {project_id}.
        Your job is to read the following document and extract its deep semantic and cognitive structures.
        Identify the primary intent, underlying reasoning patterns, unstated assumptions, explicit conclusions, and key entity relationships.

        DOCUMENT TEXT:
        {document_text}
        """
        response = await self._execute_with_fallback(prompt, project_id, CognitiveInsights, 0.1, 35.0, 30)
        if response:
            return response
        return CognitiveInsights(
            reasoning_patterns=[],
            intent="Analysis failed — all AI models were temporarily unavailable. Please retry.",
            assumptions=[],
            conclusions=[],
            relationships=[],
        )

    # STAGE 4: Similarity Evaluation
    async def stage_evaluate_similarity(self, project_id: str, document_id: str, document_summary: str, top_k: int = 5, score_threshold: float = 0.75) -> List[SimilarityMatch]:
        if self.mock_mode:
            return [SimilarityMatch(document_id="mock_similar_doc_id", similarity_score=0.92, overlapping_topics=["Mock Topic A", "Mock Topic B"])]
        try:
            vector = await self.embeddings.aembed_query(document_summary)
            matches = await pinecone_adapter.query_vectors(project_id=project_id, query_vector=vector, top_k=top_k)
            candidates = []
            for match in matches:
                match_doc_id = match.metadata.get("document_id") if match.metadata else None
                if match.score >= score_threshold and match_doc_id and match_doc_id != document_id:
                    candidates.append({"document_id": match_doc_id, "score": match.score, "summary": match.metadata.get("summary", "")})
            if not candidates:
                return []
            prompt = f"""
            You are a semantic analysis agent serving project {project_id}.
            I will provide you with a target document summary, and summaries of other similar documents.
            Your job is to identify the overlapping topics between the target document and each similar document.

            TARGET DOCUMENT (ID: {document_id}):
            {document_summary}

            SIMILAR DOCUMENTS:
            """
            for cand in candidates:
                prompt += f"\nDocument ID: {cand['document_id']} (Similarity: {cand['score']}):\n{cand['summary']}\n"
            response = await self._execute_with_fallback(prompt, project_id, SimilarityReport, 0.0, 30.0, 20)
            if not response:
                return []
            final_matches = []
            for llm_match in response.matches:
                score = next((c['score'] for c in candidates if c['document_id'] == llm_match.document_id), 0.0)
                final_matches.append(SimilarityMatch(document_id=llm_match.document_id, similarity_score=score, overlapping_topics=llm_match.overlapping_topics))
            return final_matches
        except Exception as e:
            logger.error(f"Failed to evaluate document similarity: {e}")
            raise

    # STAGE 5: Entity Connection
    async def stage_connect_entities(self, project_id: str, ucd_content: str, extracted_entities: List[Dict[str, Any]]) -> List[EntityLink]:
        if self.mock_mode:
            return [EntityLink(source_entity_id=extracted_entities[0].get("id", "entity_1") if extracted_entities else "entity_1", target_entity_id="entity_2", relationship="subsidiary of", score=0.6, valid_from=None, valid_to=None)]
        entities_context = "\n".join([f"ID: {e.get('id')} - {e.get('name')} ({e.get('type')})" for e in extracted_entities])
        prompt = f"""
        You are the ConnectorAgent for project {project_id}.
        Identify relationships between the following entities based on the text.
        
        ENTITIES:
        {entities_context}
        
        TEXT:
        <untrusted_document_content>
        {ucd_content}
        </untrusted_document_content>
        
        SCORING RULES:
        - Exact identity match: 1.0
        - High confidence semantic relationship: 0.8
        - Direct causal link identified in text: 0.6
        - Merely co-mentioned in the same sentence: 0.3
        
        Also extract any temporal boundaries (`valid_from`, `valid_to`) if explicitly stated.
        """
        response = await self._execute_with_fallback(prompt, project_id, ConnectorAgentResponse, 0.0, 20.0, 15)
        if response:
            return response.links
        return []

    # ORCHESTRATION
    async def process_chunk(self, project_id: str, chunk_text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            claims_task = asyncio.create_task(self.stage_extract_claims(project_id, chunk_text, metadata=metadata))
            summary_task = asyncio.create_task(self.stage_summarize_chunk(project_id, chunk_text))
            claims, summary = await asyncio.gather(claims_task, summary_task)
            return {"summary": summary, "claims": [claim.model_dump() for claim in claims]}
        except Exception as e:
            logger.error(f"[Pipeline] Chunk processing failed for project={project_id}: {e}")
            return {"summary": "Extraction failed due to API limits.", "claims": []}

    async def process_full_document(self, project_id: str, raw_text: str) -> Dict[str, Any]:
        try:
            cognitive_insights = await self.stage_cognitive_analysis(project_id, raw_text)
            return {"cognitive_insights": cognitive_insights}
        except Exception as e:
            logger.error(f"[Pipeline] Full document processing failed for project={project_id}: {e}")
            return {"cognitive_insights": None}

pipeline = AgentPipeline()

# Aliases for backwards compatibility during transition
orchestrator = pipeline
cognitive_agent = pipeline
connector_agent = pipeline
extractor_agent = pipeline
similarity_agent = pipeline
summarizer_agent = pipeline

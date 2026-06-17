import logging
from typing import List, Dict, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.vector_store.pinecone_adapter import pinecone_adapter
from app.core.config import settings

logger = logging.getLogger(__name__)

class CandidateSelector:
    def __init__(self):
        self.mock_mode = False
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(model=settings.GEMINI_EMBEDDING_MODEL)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini Embeddings for CandidateSelector. Running in mock mode: {e}")
            self.mock_mode = True

    async def select_candidates(self, project_id: str, claim_text: str, top_k: int = 5, score_threshold: float = 0.80) -> List[Dict[str, Any]]:
        """
        Stage 2: Embeds the incoming claim and queries Pinecone for highly similar cross-modal claims.
        """
        if self.mock_mode:
            logger.info(f"[MOCK SELECTOR] Selecting candidates for project {project_id}")
            return [
                {"id": "mock_candidate_1", "score": 0.95, "metadata": {"fact": "Mock fact A", "modality": "pdf", "source_span": "Mock fact A"}}
            ]
            
        try:
            # 1. Embed the claim
            vector = await self.embeddings.aembed_query(claim_text)
            
            # 2. Query Pinecone with strict project isolation
            matches = await pinecone_adapter.query_vectors(project_id=project_id, query_vector=vector, top_k=top_k)
            
            # 3. Filter by similarity threshold
            candidates = []
            for match in matches:
                if match.score >= score_threshold:
                    candidates.append({
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata
                    })
                    
            logger.info(f"Stage 2 found {len(candidates)} candidates for project {project_id} above threshold {score_threshold}")
            return candidates
            
        except Exception as e:
            logger.error(f"Failed to select candidates: {e}")
            raise

candidate_selector = CandidateSelector()

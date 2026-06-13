import logging
from pinecone import Pinecone
from app.core.config import settings

logger = logging.getLogger(__name__)

class PineconeAdapter:
    def __init__(self):
        # In local dev with mock keys, we don't want to crash on startup
        # We initialize it lazily or catch the error.
        self._pc = None
        self._index = None
        self.index_name = "omnimind-v2"  # Global serverless index name
        
        try:
            if settings.PINECONE_API_KEY and not settings.PINECONE_API_KEY.startswith("mock-"):
                self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                self._index = self._pc.Index(self.index_name)
                logger.info("Pinecone client initialized successfully.")
            else:
                logger.warning("Running with mock Pinecone key. Vector operations will be mocked.")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")

    async def upsert_vectors(self, project_id: str, vectors: list[dict]):
        """
        Upsert vectors enforcing Layer 4 namespace isolation by project_id.
        Vectors should be a list of dicts: {"id": "str", "values": [float], "metadata": {}}
        """
        if not self._index:
            logger.info(f"[MOCK PINECONE] Upserting {len(vectors)} vectors to namespace {project_id}")
            return
            
        try:
            # Pinecone client does not have native async yet, so we use sync wrapper
            # For high-throughput production, we'd use an executor or the REST API via HTTPX
            self._index.upsert(vectors=vectors, namespace=str(project_id))
        except Exception as e:
            logger.error(f"Failed to upsert vectors to Pinecone: {e}")
            raise

    async def query_vectors(self, project_id: str, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """
        Query vectors strictly within the project's namespace.
        """
        if not self._index:
            logger.info(f"[MOCK PINECONE] Querying vector in namespace {project_id}")
            return []
            
        try:
            response = self._index.query(
                vector=query_vector,
                namespace=str(project_id),
                top_k=top_k,
                include_metadata=True
            )
            return response.matches
        except Exception as e:
            logger.error(f"Failed to query Pinecone: {e}")
            raise

pinecone_adapter = PineconeAdapter()

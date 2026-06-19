import logging
import asyncio
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
            from pinecone import ServerlessSpec
            if settings.PINECONE_API_KEY and not settings.PINECONE_API_KEY.startswith("mock-"):
                self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                
                if self.index_name not in self._pc.list_indexes().names():
                    logger.info(f"Creating Pinecone index '{self.index_name}' (this may take a minute)...")
                    self._pc.create_index(
                        name=self.index_name,
                        dimension=3072,  # Match gemini-embedding-001 dimensions
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        )
                    )
                    logger.info("Pinecone index created successfully.")

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
            
        for attempt in range(5):
            try:
                await asyncio.to_thread(
                    self._index.upsert,
                    vectors=vectors,
                    namespace=str(project_id)
                )
                return
            except Exception as e:
                logger.error(f"Failed to upsert vectors to Pinecone (attempt {attempt+1}): {e}")
                if "Failed to resolve" in str(e) or "NameResolutionError" in str(e):
                    try:
                        self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                        self._index = self._pc.Index(self.index_name)
                    except Exception as inner_e:
                        logger.error(f"Failed to reinitialize Pinecone index: {inner_e}")
                if attempt == 4:
                    logger.error("Pinecone upsert failed completely after 5 attempts. Gracefully ignoring to allow pipeline to continue.")
                    return
                await asyncio.sleep(2 ** attempt + 3)

    async def query_vectors(self, project_id: str, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """
        Query vectors strictly within the project's namespace.
        """
        if not self._index:
            logger.info(f"[MOCK PINECONE] Querying vector in namespace {project_id}")
            return []
            
        for attempt in range(5):
            try:
                response = await asyncio.to_thread(
                    self._index.query,
                    vector=query_vector,
                    namespace=str(project_id),
                    top_k=top_k,
                    include_metadata=True
                )
                return response.matches
            except Exception as e:
                logger.error(f"Failed to query Pinecone (attempt {attempt+1}): {e}")
                if "Failed to resolve" in str(e) or "NameResolutionError" in str(e):
                    try:
                        self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                        self._index = self._pc.Index(self.index_name)
                    except Exception as inner_e:
                        logger.error(f"Failed to reinitialize Pinecone index: {inner_e}")
                if attempt == 4:
                    raise
                await asyncio.sleep(2 ** attempt + 3)

    async def fetch_all(self, project_id: str, type: str = "claim") -> list[dict]:
        """
        Fetches all vectors of a specific type in the given namespace.
        Uses a dummy zero vector query with high top_k to retrieve all items.
        Returns the metadata dicts.
        """
        if not self._index:
            logger.info(f"[MOCK PINECONE] Fetching all {type}s from namespace {project_id}")
            return []
            
        try:
            dimension = 3072
            dummy_vector = [1e-5] * dimension
            
            for attempt in range(5):
                try:
                    response = await asyncio.to_thread(
                        self._index.query,
                        vector=dummy_vector,
                        namespace=str(project_id),
                        top_k=10000,
                        include_metadata=True,
                        include_values=True,
                        filter={"type": type}
                    )
                    return [{**match.metadata, "values": match.values} for match in response.matches if match.metadata]
                except Exception as e:
                    logger.error(f"Failed to fetch_all from Pinecone (attempt {attempt+1}): {e}")
                    if "Failed to resolve" in str(e) or "NameResolutionError" in str(e):
                        # Re-initialize index client in case of stale host resolution
                        try:
                            self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                            self._index = self._pc.Index(self.index_name)
                        except Exception as inner_e:
                            logger.error(f"Failed to reinitialize Pinecone index: {inner_e}")
                    if attempt == 4:
                        logger.error("Pinecone fetch_all failed completely after 5 attempts. Returning empty list.")
                        return []
                    await asyncio.sleep(2 ** attempt + 3)
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_all from Pinecone: {e}")
            return []

pinecone_adapter = PineconeAdapter()

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class SectionChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initializes the chunker using tiktoken to approximate the 512-token limit
        required by embedding models, with a slight overlap to preserve context.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.token_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def chunk_document(self, text: str, pages: list[dict] = None, utterances: list[dict] = None) -> list[dict]:
        """
        Takes raw document text and uses tiktoken to ensure no chunk exceeds the 512-token limit.
        Can process page-segmented or timestamp-segmented text.
        """
        if not text or not text.strip():
            return []
            
        try:
            final_chunks = []
            if pages:
                for page in pages:
                    page_text = page.get("text", "")
                    if not page_text.strip():
                        continue
                    chunks = self.token_splitter.create_documents([page_text])
                    for c in chunks:
                        final_chunks.append({
                            "text": c.page_content,
                            "page_number": page.get("page_number")
                        })
            elif utterances:
                for utterance in utterances:
                    u_text = utterance.get("text", "")
                    if not u_text.strip():
                        continue
                    chunks = self.token_splitter.create_documents([u_text])
                    for c in chunks:
                        start_time = utterance.get("start_time")
                        if isinstance(start_time, str) and start_time.endswith('s'):
                            try:
                                start_time = float(start_time[:-1])
                            except ValueError:
                                start_time = None
                        final_chunks.append({
                            "text": c.page_content,
                            "timestamp_start_seconds": start_time,
                            "speaker_id": utterance.get("speaker_id")
                        })
            else:
                chunks = self.token_splitter.create_documents([text])
                for c in chunks:
                    final_chunks.append({
                        "text": c.page_content,
                        "page_number": None
                    })
            logger.info(f"Successfully split text into {len(final_chunks)} chunks.")
            return final_chunks
        except Exception as e:
            logger.error(f"Failed to chunk document: {e}")
            raise

section_chunker = SectionChunker()

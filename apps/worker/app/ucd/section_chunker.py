import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

logger = logging.getLogger(__name__)

class SectionChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initializes the chunker using tiktoken to approximate the 512-token limit
        required by embedding models, with a slight overlap to preserve context.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Split by headings first
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )
        
        # Fallback to 512 tokens for long sections
        self.token_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def chunk_document(self, text: str) -> list[str]:
        """
        Takes raw document text, splits it by Markdown headings first, 
        then uses tiktoken to ensure no chunk exceeds the 512-token limit.
        """
        if not text or not text.strip():
            return []
            
        try:
            # 1. Split by headings
            header_splits = self.markdown_splitter.split_text(text)
            
            # 2. Split any oversized chunks by tokens
            chunks = self.token_splitter.split_documents(header_splits)
            
            # Extract raw string content for simple return type
            final_chunks = [chunk.page_content for chunk in chunks]
            
            logger.info(f"Successfully split text into {len(final_chunks)} chunks.")
            return final_chunks
        except Exception as e:
            logger.error(f"Failed to chunk document: {e}")
            raise

section_chunker = SectionChunker()

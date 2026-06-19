from typing import List
from pydantic import BaseModel, Field

class SimilarityMatch(BaseModel):
    document_id: str = Field(description="The ID of the matched document")
    similarity_score: float = Field(description="The semantic similarity score")
    overlapping_topics: List[str] = Field(description="Topics or concepts that overlap between the two documents")

class SimilarityReport(BaseModel):
    matches: List[SimilarityMatch] = Field(description="List of similar documents found")

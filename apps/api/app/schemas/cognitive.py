from typing import List
from pydantic import BaseModel, Field

class EntityRelationship(BaseModel):
    entity_a: str
    relationship: str
    entity_b: str

class CognitiveInsights(BaseModel):
    reasoning_patterns: List[str] = Field(description="The underlying reasoning or logic used in the text.")
    intent: str = Field(description="The primary intent or goal of the document.")
    assumptions: List[str] = Field(description="Implicit assumptions made by the author.")
    conclusions: List[str] = Field(description="Explicit conclusions drawn in the document.")
    relationships: List[EntityRelationship] = Field(description="Key entities and their relationships.")

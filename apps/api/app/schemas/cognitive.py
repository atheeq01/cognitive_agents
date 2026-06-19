from typing import List, Optional
from pydantic import BaseModel, Field

class EntityRelationship(BaseModel):
    entity_a: str
    relationship: str
    entity_b: str

class CognitiveInsights(BaseModel):
    reasoning_patterns: List[str] = Field(default_factory=list, description="The underlying reasoning or logic used in the text.")
    intent: Optional[str] = Field(default=None, description="The primary intent or goal of the document.")
    intents: List[str] = Field(default_factory=list, description="List of intents for project-level synthesis.")
    assumptions: List[str] = Field(default_factory=list, description="Implicit assumptions made by the author.")
    conclusions: List[str] = Field(default_factory=list, description="Explicit conclusions drawn in the document.")
    relationships: List[EntityRelationship] = Field(default_factory=list, description="Key entities and their relationships.")

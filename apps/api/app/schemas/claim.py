from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.report import SourceLocation


class Claim(BaseModel):
    claim_id: str = Field(description="A unique ID for this claim")
    fact: str = Field(description="The atomic statement or fact extracted from the text")
    source_location: Optional['SourceLocation'] = Field(None, description="The exact source location of this claim")


class ClaimExtractorResponse(BaseModel):
    claims: List[Claim]

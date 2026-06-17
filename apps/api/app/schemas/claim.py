from typing import List, Optional
from pydantic import BaseModel, Field

class ModalityContext(BaseModel):
    modality: str = Field(description="The source modality: pdf, image, audio, docx, etc.")
    speaker_id: Optional[str] = Field(None, description="The speaker ID if modality is audio")
    timestamp: Optional[str] = Field(None, description="The timestamp or page number of the claim")

class Claim(BaseModel):
    claim_id: str = Field(description="A unique ID for this claim")
    fact: str = Field(description="The atomic statement or fact extracted from the text")
    source_span: str = Field(description="The exact quote from the text that proves this claim")
    speaker_id: Optional[str] = Field(None, description="The person who stated this claim, if applicable")
    modality_context: Optional[ModalityContext] = Field(None, description="The modality context from which the claim was extracted")

class ClaimExtractorResponse(BaseModel):
    claims: List[Claim]

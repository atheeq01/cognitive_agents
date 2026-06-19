from typing import List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime

class SourceLocation(BaseModel):
    document_id: str
    document_name: str
    modality: Literal["pdf", "docx", "audio", "video", "image"]

    # For documents (pdf/docx)
    page_number: Optional[int] = None
    line_number: Optional[int] = None

    # For audio/video
    timestamp_start_seconds: Optional[float] = None
    timestamp_end_seconds: Optional[float] = None
    speaker_id: Optional[str] = None

    # For images
    bounding_box: Optional[List[float]] = None  # [x_min, y_min, x_max, y_max], normalized 0-1

    # Universal — used for click-to-highlight regardless of modality
    exact_quote: str

class ContradictionFinding(BaseModel):
    topic: str                          # short human label, e.g. "Q3 revenue figure"
    conflict_type: Literal["factual", "temporal", "definitional", "logical", "cross-modal"]
    claim_a: str
    claim_a_source: SourceLocation
    claim_b: str
    claim_b_source: SourceLocation
    explanation: str                    # plain-English: why this matters

class AgreementFinding(BaseModel):
    topic: str
    supporting_claims: List[str]
    supporting_sources: List[SourceLocation]

from app.schemas.cognitive import CognitiveInsights

class ProjectReport(BaseModel):
    project_id: str
    document_count: int
    modalities_included: List[str]
    unified_summary: str                # one project-wide narrative, not concatenated doc summaries
    cognitive_synthesis: CognitiveInsights   # merged across all docs, not per-doc duplicates
    contradictions: List[ContradictionFinding]
    agreements: List[AgreementFinding]
    generated_at: datetime

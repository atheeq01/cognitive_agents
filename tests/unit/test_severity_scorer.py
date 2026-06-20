import pytest
from app.agents.contradiction_pipeline.severity_scorer import severity_scorer

@pytest.mark.unit
class TestSeverityScorer:
    def test_cross_modal_pdf_audio_is_critical(self):
        claim_a = {"modality": "pdf"}
        claim_b = {"metadata": {"modality": "audio"}}
        assert severity_scorer.score_conflict(claim_a, claim_b, "factual") == "CRITICAL"

    def test_cross_modal_docx_image_is_critical(self):
        claim_a = {"modality": "image"}
        claim_b = {"metadata": {"modality": "docx"}}
        assert severity_scorer.score_conflict(claim_a, claim_b, "temporal") == "CRITICAL"

    def test_same_modal_factual_is_high(self):
        claim_a = {"modality": "pdf"}
        claim_b = {"metadata": {"modality": "pdf"}}
        assert severity_scorer.score_conflict(claim_a, claim_b, "factual") == "HIGH"

    def test_same_modal_temporal_is_high(self):
        claim_a = {"modality": "audio"}
        claim_b = {"metadata": {"modality": "audio"}}
        assert severity_scorer.score_conflict(claim_a, claim_b, "temporal") == "HIGH"

    def test_definitional_is_low(self):
        claim_a = {"modality": "pdf"}
        claim_b = {"metadata": {"modality": "pdf"}}
        assert severity_scorer.score_conflict(claim_a, claim_b, "definitional") == "LOW"

    def test_logical_is_low(self):
        claim_a = {"modality": "audio"}
        claim_b = {"metadata": {"modality": "audio"}}
        assert severity_scorer.score_conflict(claim_a, claim_b, "logical") == "LOW"

    def test_unknown_modality_fallback(self):
        claim_a = {}
        claim_b = {}
        # They match ("unknown" == "unknown") so it's not cross modal
        assert severity_scorer.score_conflict(claim_a, claim_b, "factual") == "HIGH"
        assert severity_scorer.score_conflict(claim_a, claim_b, "stylistic") == "LOW"

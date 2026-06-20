import pytest
from app.services.report_generator import report_generator
from app.schemas.cognitive import CognitiveInsights
from app.schemas.similarity import SimilarityMatch

@pytest.fixture
def base_insights():
    return CognitiveInsights(
        intent="Test intent",
        reasoning_patterns=[],
        assumptions=[],
        conclusions=[],
        relationships=[]
    )

@pytest.mark.unit
class TestReportGenerator:
    def test_report_contains_document_name(self, base_insights):
        md = report_generator.generate_markdown_report(
            document_name="Test Doc",
            upload_timestamp="2024-01-01",
            summary="Test summary",
            cognitive_insights=base_insights,
            similarities=[],
            contradictions=[]
        )
        assert "Test Doc" in md
        assert "Test summary" in md
        
    def test_report_no_similarities(self, base_insights):
        md = report_generator.generate_markdown_report(
            document_name="Test Doc", upload_timestamp="", summary="",
            cognitive_insights=base_insights, similarities=[], contradictions=[]
        )
        assert "No significant overlaps" in md
        
    def test_report_no_contradictions(self, base_insights):
        md = report_generator.generate_markdown_report(
            document_name="Test Doc", upload_timestamp="", summary="",
            cognitive_insights=base_insights, similarities=[], contradictions=[]
        )
        assert "No contradictions detected" in md
        
    def test_report_with_similarities(self, base_insights):
        sims = [
            SimilarityMatch(
                document_id="doc_xyz",
                similarity_score=0.95,
                overlapping_topics=["Pricing", "Costs"]
            )
        ]
        md = report_generator.generate_markdown_report(
            document_name="Test Doc", upload_timestamp="", summary="",
            cognitive_insights=base_insights, similarities=sims, contradictions=[]
        )
        assert "doc_xyz" in md
        assert "0.95" in md
        assert "Pricing" in md

    def test_report_with_contradictions(self, base_insights):
        contras = [
            {
                "conflicting_document_id": "doc_123",
                "quote_a": "It is red",
                "quote_b": "It is blue",
                "reasoning": "Colors do not match"
            }
        ]
        md = report_generator.generate_markdown_report(
            document_name="Test Doc", upload_timestamp="", summary="",
            cognitive_insights=base_insights, similarities=[], contradictions=contras
        )
        assert "doc_123" in md
        assert "It is red" in md
        assert "It is blue" in md
        assert "Colors do not match" in md

    def test_report_cognitive_insights(self, base_insights):
        base_insights.reasoning_patterns = ["Pattern A"]
        md = report_generator.generate_markdown_report(
            document_name="Test Doc", upload_timestamp="", summary="",
            cognitive_insights=base_insights, similarities=[], contradictions=[]
        )
        assert "Test intent" in md
        assert "Pattern A" in md

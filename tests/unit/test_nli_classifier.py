import pytest
from unittest.mock import AsyncMock, patch
from app.agents.contradiction_pipeline.nli_classifier import NLIClassifier, NLIResult

@pytest.fixture
def classifier():
    return NLIClassifier()

@pytest.mark.unit
@pytest.mark.asyncio
class TestNLIClassifier:
    async def test_classify_contradiction_with_evidence(self, classifier):
        claim_a = {"fact": "A says X"}
        claim_b = {"fact": "B says Y"}
        
        mock_result = NLIResult(
            relation="CONTRADICTION",
            conflict_type="factual",
            evidence_a="X",
            evidence_b="Y"
        )
        
        with patch.object(classifier, '_execute_with_fallback', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await classifier.classify_pair(claim_a, claim_b)
            assert result.relation == "CONTRADICTION"
            assert result.evidence_a == "X"

    async def test_contradiction_without_evidence_falls_to_neutral(self, classifier):
        claim_a = "A says X"
        claim_b = "B says Y"
        
        mock_result = NLIResult(
            relation="CONTRADICTION",
            evidence_a=None,
            evidence_b=None
        )
        
        with patch.object(classifier, '_execute_with_fallback', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await classifier.classify_pair(claim_a, claim_b)
            # The classifier overrides it to NEUTRAL if evidence is missing
            assert result.relation == "NEUTRAL"

    async def test_classify_entailment(self, classifier):
        mock_result = NLIResult(relation="ENTAILMENT")
        
        with patch.object(classifier, '_execute_with_fallback', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await classifier.classify_pair("X", "X")
            assert result.relation == "ENTAILMENT"

    async def test_classify_with_json_source_location(self, classifier):
        claim_a = {
            "fact": "A says X",
            "source_location": '{"modality": "audio", "speaker_id": "Spk1", "exact_quote": "A says X"}'
        }
        claim_b = "B says Y"
        
        mock_result = NLIResult(relation="NEUTRAL")
        
        with patch.object(classifier, '_execute_with_fallback', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            await classifier.classify_pair(claim_a, claim_b)
            
            # Verify the prompt string extracted the JSON properly
            prompt_sent = mock_exec.call_args.kwargs['prompt']
            assert "Modality: audio" in prompt_sent
            assert "Speaker: Spk1" in prompt_sent

    async def test_all_models_fail_returns_neutral(self, classifier):
        with patch.object(classifier, '_execute_with_fallback', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = None
            result = await classifier.classify_pair("A", "B")
            assert result.relation == "NEUTRAL"

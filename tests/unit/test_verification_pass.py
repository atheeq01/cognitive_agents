import pytest
from unittest.mock import AsyncMock, patch
from app.agents.contradiction_pipeline.verification_pass import VerificationPass, VerificationResult

@pytest.fixture
def verifier():
    return VerificationPass()

@pytest.mark.unit
@pytest.mark.asyncio
class TestVerificationPass:
    async def test_verify_true_contradiction(self, verifier):
        mock_result = VerificationResult(is_contradiction=True, reasoning="Yes")
        with patch.object(verifier, '_execute_with_fallback', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await verifier.verify_conflict("A", "B")
            assert result.is_contradiction is True

    async def test_verify_false_alarm(self, verifier):
        mock_result = VerificationResult(is_contradiction=False, reasoning="No")
        with patch.object(verifier, '_execute_with_fallback', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await verifier.verify_conflict("A", "B")
            assert result.is_contradiction is False

    async def test_all_models_fail_safe_default(self, verifier):
        with patch.object(verifier, '_execute_with_fallback', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = None
            result = await verifier.verify_conflict("A", "B")
            assert result.is_contradiction is False
            assert "Failed to verify" in result.reasoning

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.pipeline import BaseAgent
from google.api_core import exceptions as google_exceptions

class DummyAgent(BaseAgent):
    def __init__(self):
        super().__init__("DummyAgent")

@pytest.mark.unit
class TestBaseAgent:
    def test_base_agent_init_models_list(self):
        agent = DummyAgent()
        # Verify primary is first
        assert agent.models_to_try[0] == agent.primary_model
        # Verify no duplicates
        assert len(agent.models_to_try) == len(set(agent.models_to_try))
        # Verify length
        assert len(agent.models_to_try) == len(agent._FALLBACK_MODELS) + (1 if agent.primary_model not in agent._FALLBACK_MODELS else 0)

    @pytest.mark.asyncio
    @patch('app.agents.pipeline.ChatGoogleGenerativeAI')
    async def test_fallback_on_timeout(self, mock_chat_cls):
        agent = DummyAgent()
        
        # Mock LLM instances
        mock_llm_1 = MagicMock()
        mock_llm_1.ainvoke = AsyncMock(side_effect=asyncio.TimeoutError())
        
        mock_llm_2 = MagicMock()
        mock_llm_2.ainvoke = AsyncMock(return_value="Success")
        
        mock_chat_cls.side_effect = [mock_llm_1, mock_llm_2]
        
        result = await agent._execute_with_fallback("prompt", "project_id", timeout=0.1)
        assert result == "Success"
        assert mock_chat_cls.call_count == 2
        # Verify cooldown was applied
        assert agent.models_to_try[0] in agent._failing_models

    @pytest.mark.asyncio
    @patch('app.agents.pipeline.ChatGoogleGenerativeAI')
    async def test_fallback_on_503(self, mock_chat_cls):
        agent = DummyAgent()
        mock_llm_1 = MagicMock()
        mock_llm_1.ainvoke = AsyncMock(side_effect=google_exceptions.ServiceUnavailable("Overloaded"))
        
        mock_llm_2 = MagicMock()
        mock_llm_2.ainvoke = AsyncMock(return_value="Success")
        
        mock_chat_cls.side_effect = [mock_llm_1, mock_llm_2]
        
        result = await agent._execute_with_fallback("prompt", "project_id")
        assert result == "Success"

    @pytest.mark.asyncio
    @patch('app.agents.pipeline.ChatGoogleGenerativeAI')
    async def test_all_models_fail_returns_none(self, mock_chat_cls):
        agent = DummyAgent()
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("Unknown Error"))
        mock_chat_cls.return_value = mock_llm
        
        result = await agent._execute_with_fallback("prompt", "project_id")
        assert result is None
        assert mock_chat_cls.call_count == len(agent.models_to_try)

    @pytest.mark.asyncio
    @patch('app.agents.pipeline.ChatGoogleGenerativeAI')
    async def test_circuit_breaker_skips_failing_model(self, mock_chat_cls):
        import time
        agent = DummyAgent()
        # Put first model in cooldown
        first_model = agent.models_to_try[0]
        agent._failing_models[first_model] = time.time() + 60
        
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value="Success")
        mock_chat_cls.return_value = mock_llm
        
        result = await agent._execute_with_fallback("prompt", "project_id")
        assert result == "Success"
        # Only tried the rest
        assert mock_chat_cls.call_count == 1

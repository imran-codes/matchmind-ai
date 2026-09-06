"""Real ADK runner and tool execution; only the remote LLM is replaced."""
"""Tests for ADK tool calling, request isolation, and failure handling."""
import asyncio
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from app.agent import ToolState, build_agent
from app.agent_runtime import analyse, AgentUnavailable
from app.config import Settings
import pytest


class ScriptedModel(BaseLlm):
    """Fake model that emits a fixed tool call and optional failure."""
    model: str = "test-model"
    fail_after_tool: bool = False
    calls: int = 0

    async def generate_content_async(self, llm_request, stream=False):
        self.calls += 1
        if self.calls == 1:
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(
                function_call=types.FunctionCall(name="predict_match", args={
                    "home_team": "Arsenal", "away_team": "Liverpool"}))]))
        elif self.fail_after_tool:
            raise RuntimeError("simulated provider outage")
        else:
            # Deliberately fabricated prose must never replace classifier probabilities.
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text="Home win 99% (test fabrication)")]))


class BrokenModel(BaseLlm):
    """Fake model that fails before the agent can produce a tool result."""
    model: str = "broken-test-model"
    async def generate_content_async(self, llm_request, stream=False):
        raise RuntimeError("simulated provider outage")
        yield


def test_real_adk_calls_tool_and_preserves_probabilities(predictor):
    """The agent should call the tool and keep the classifier probabilities."""
    result = asyncio.run(analyse(predictor, Settings(), "Predict Arsenal against Liverpool", model=ScriptedModel()))
    assert result.tool_calls == ["predict_match"]
    assert result.predictions[0].probabilities == predictor.predict("Arsenal", "Liverpool")["probabilities"]
    assert "99%" in result.agent_commentary
    assert result.status == "complete"


def test_failure_after_tool_preserves_results(predictor):
    """If the model fails after a tool call, keep the verified prediction."""
    result = asyncio.run(analyse(predictor, Settings(), "Predict Arsenal against Liverpool", model=ScriptedModel(fail_after_tool=True)))
    assert result.status == "partial"
    assert len(result.predictions) == 1
    assert result.agent_commentary == ""


def test_failure_before_tool_is_explicit(predictor):
    """If the model never reaches a tool call, report the outage clearly."""
    with pytest.raises(AgentUnavailable):
        asyncio.run(analyse(predictor, Settings(), "Predict Arsenal against Liverpool", model=BrokenModel()))


def test_tool_limit_is_enforced_in_python(predictor):
    """Stop the request once it exceeds the allowed tool budget."""
    state = ToolState()
    agent = build_agent(predictor, ScriptedModel(), state, max_calls=2)
    predict = agent.tools[1]
    predict("Arsenal", "Liverpool")
    predict("Arsenal", "Arsenal")
    rejected = predict("Chelsea", "Man City")
    assert "error" in rejected
    assert len(state.predictions) == 1


def test_requests_do_not_share_results(predictor):
    """Each agent request should have isolated tool state."""
    async def run():
        return await asyncio.gather(*[analyse(predictor, Settings(), "Predict Arsenal against Liverpool", model=ScriptedModel()) for _ in range(2)])
    a, b = asyncio.run(run())
    assert a.request_id != b.request_id
    assert len(a.predictions) == len(b.predictions) == 1

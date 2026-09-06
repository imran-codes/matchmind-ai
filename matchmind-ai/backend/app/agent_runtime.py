"""Bounded, stateless ADK runs. No shared chat history or credential files."""
import asyncio
from contextlib import aclosing
from uuid import uuid4

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import ToolState, build_agent
from app.config import Settings
from app.schemas import Analysis


class AgentUnavailable(Exception):
    pass


async def analyse(predictor, settings: Settings, message: str, model=None) -> Analysis:
    if model is None and (not settings.agent_enabled or not settings.gemini_model):
        raise AgentUnavailable("Enable the ADK agent and set GEMINI_MODEL first")
    request_id = str(uuid4())
    state = ToolState()
    sessions = InMemorySessionService()
    agent = build_agent(predictor, model or settings.gemini_model, state, settings.max_tool_calls)
    runner = Runner(agent=agent, app_name="matchmind", session_service=sessions)
    session = await sessions.create_session(app_name="matchmind", user_id=request_id)
    commentary, input_tokens, output_tokens = "", 0, 0
    failure = False
    try:
        async with asyncio.timeout(settings.agent_timeout):
            async with aclosing(runner.run_async(
                user_id=request_id, session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text=message)]),
                run_config=RunConfig(max_llm_calls=settings.max_llm_calls),
            )) as events:
                async for event in events:
                    usage = event.usage_metadata
                    if usage:
                        input_tokens += usage.prompt_token_count or 0
                        output_tokens += (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
                    if event.is_final_response() and event.content:
                        commentary = "\n".join(part.text for part in event.content.parts or []
                                               if part.text and not part.thought)[:3000]
    except Exception:
        # Do not log raw prompts, credentials or provider errors. No silent fake-agent fallback.
        failure = True
        commentary = ""
    finally:
        await sessions.delete_session(app_name="matchmind", user_id=request_id, session_id=session.id)
        await runner.close()
    if failure and not state.predictions:
        raise AgentUnavailable("Agent unavailable or request budget exceeded. Retry or use direct prediction.")
    return Analysis(
        request_id=request_id,
        status="partial" if failure else "complete" if state.predictions else "no_prediction",
        message=("Agent did not finish; verified tool results are shown." if failure else
                 "Prediction cards come directly from the classifier tool." if state.predictions else
                 "No model prediction was produced. Provide two supported teams."),
        agent_commentary=commentary, predictions=state.predictions, tool_calls=state.calls,
        input_tokens=input_tokens, output_tokens=output_tokens,
    )

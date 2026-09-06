"""ADK development UI entrypoint. Run: PYTHONPATH=backend adk web backend/agents"""
"""ADK development agent that wraps the football prediction tools."""
from app.agent import ToolState, build_agent
from app.config import Settings
from app.prediction import PredictionService

settings = Settings()
if not settings.gemini_model:
    raise RuntimeError("Set GEMINI_MODEL before starting ADK's development UI")

# The development UI shares the root agent across turns; reset tool state before each run.
state = ToolState()
# Build the same root agent used by the backend, but for the local ADK web UI.
root_agent = build_agent(PredictionService(settings.artifact_dir), settings.gemini_model, state)

def reset_state(callback_context):
    """Clear the shared state between interactive ADK turns."""
    state.predictions.clear()
    state.calls.clear()
    state.attempts = 0

root_agent.before_agent_callback = reset_state

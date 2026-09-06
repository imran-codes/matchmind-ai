"""Read app settings from environment variables."""
import os
from dataclasses import dataclass, field
from pathlib import Path

# Path to the backend package root, used as the default artifact location.
BACKEND = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    artifact_dir: Path = field(default_factory=lambda: Path(os.getenv("ARTIFACT_DIR", str(BACKEND / "artifacts"))))  # Trained model files.
    static_dir: Path = field(default_factory=lambda: Path(os.getenv("STATIC_DIR", str(BACKEND.parent / "frontend" / "dist"))))  # Built React app.
    agent_enabled: bool = field(default_factory=lambda: os.getenv("AGENT_ENABLED", "false").lower() == "true")  # Toggle ADK on or off.
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", ""))  # Exact Vertex/Gemini model ID.
    agent_timeout: float = 60.0  # Max seconds a request may spend in the agent.
    max_llm_calls: int = 4  # Limit model turns per request.
    max_tool_calls: int = 6  # Limit tool usage per request.

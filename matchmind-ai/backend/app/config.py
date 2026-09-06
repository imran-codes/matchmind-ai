"""Environment configuration. No credentials are stored in source."""
import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    artifact_dir: Path = field(default_factory=lambda: Path(os.getenv("ARTIFACT_DIR", str(BACKEND / "artifacts"))))
    static_dir: Path = field(default_factory=lambda: Path(os.getenv("STATIC_DIR", str(BACKEND.parent / "frontend" / "dist"))))
    agent_enabled: bool = field(default_factory=lambda: os.getenv("AGENT_ENABLED", "false").lower() == "true")
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", ""))
    agent_timeout: float = 60.0
    max_llm_calls: int = 4
    max_tool_calls: int = 6

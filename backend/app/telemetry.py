"""App-owned logs are deliberately allowlisted; no raw prompts or agent outputs."""
import json
import logging
from datetime import UTC, datetime

logger = logging.getLogger("matchmind")
FIELDS = {"request_id", "status", "latency_ms", "model_version", "prompt_version",
          "input_tokens", "output_tokens", "prediction_count", "tool_count"}


def emit(event: str, **fields) -> None:
    logger.info(json.dumps({"event": event, "severity": "INFO",
                            "timestamp": datetime.now(UTC).isoformat(),
                            **{key: value for key, value in fields.items() if key in FIELDS}}))

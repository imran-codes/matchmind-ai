"""Write structured logs with only safe, allowlisted fields."""
import json
import logging
from datetime import UTC, datetime

logger = logging.getLogger("matchmind")
# Only these fields are emitted so raw prompts and sensitive data stay out of logs.
FIELDS = {"request_id", "status", "latency_ms", "model_version", "prompt_version",
          "input_tokens", "output_tokens", "prediction_count", "tool_count"}


def emit(event: str, **fields) -> None:
    """Send one structured JSON log line for a completed app event."""
    logger.info(json.dumps({"event": event, "severity": "INFO",
                            "timestamp": datetime.now(UTC).isoformat(),
                            **{key: value for key, value in fields.items() if key in FIELDS}}))

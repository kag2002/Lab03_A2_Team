import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TRACE_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "agent_traces.jsonl"
MAX_STRING_LENGTH = 500
MAX_LIST_ITEMS = 20
MAX_DICT_ITEMS = 30
SAFE_TOKEN_FIELDS = {
    "max_tokens",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
}
SENSITIVE_FIELD_RE = re.compile(
    r"(api[_-]?key|secret|password|credential|private[_-]?key|access[_-]?token|refresh[_-]?token)",
    re.IGNORECASE,
)
SECRET_VALUE_RE = re.compile(
    r"\b(?:sk|sk-ant|ghp|xoxb)-[A-Za-z0-9_\-]{12,}\b",
    re.IGNORECASE,
)
logger = logging.getLogger("app.monitoring.trace_logger")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_preview(value: Any, max_length: int = MAX_STRING_LENGTH) -> Any:
    """Redact and truncate values before writing them to local trace logs."""
    redacted = _redact_for_trace(value)
    return _truncate(redacted, max_length=max_length)


def _redact_for_trace(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text not in SAFE_TOKEN_FIELDS and SENSITIVE_FIELD_RE.search(key_text):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = _redact_for_trace(item)
        return redacted

    if isinstance(value, list):
        return [_redact_for_trace(item) for item in value]

    if isinstance(value, str):
        return SECRET_VALUE_RE.sub("[REDACTED]", value)

    return value


def _truncate(value: Any, max_length: int) -> Any:
    if isinstance(value, str):
        if len(value) <= max_length:
            return value
        return value[:max_length] + f"...[truncated {len(value) - max_length} chars]"

    if isinstance(value, list):
        items = [_truncate(item, max_length=max_length) for item in value[:MAX_LIST_ITEMS]]
        if len(value) > MAX_LIST_ITEMS:
            items.append(f"...[truncated {len(value) - MAX_LIST_ITEMS} items]")
        return items

    if isinstance(value, dict):
        truncated: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_DICT_ITEMS:
                truncated["...[truncated]"] = f"{len(value) - MAX_DICT_ITEMS} more fields"
                break
            truncated[str(key)] = _truncate(item, max_length=max_length)
        return truncated

    return value


class JsonTraceLogger:
    def write_trace(self, trace: dict[str, Any]) -> None:
        try:
            TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with TRACE_LOG_PATH.open("a", encoding="utf-8") as file:
                file.write(json.dumps(trace, ensure_ascii=False, default=str) + "\n")
        except OSError as exc:
            logger.warning(f"Failed to write JSON trace log: {exc}")


json_trace_logger = JsonTraceLogger()

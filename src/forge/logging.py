"""FORGE JSONL structured logger.

Produces append-only JSONL log files with trace IDs.
This is the observability foundation — Grafana deferred to V1.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forge.config import ForgeConfig


class ForgeLogger:
    """Structured JSONL logger with trace ID support."""

    def __init__(self, log_path: Path, level: str = "INFO") -> None:
        self.log_path = log_path
        self.level = level
        self._trace_id = uuid.uuid4().hex[:16]
        log_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def trace_id(self) -> str:
        return self._trace_id

    def _write(self, level: str, event: str, **fields: Any) -> dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "trace_id": self._trace_id,
            **fields,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
        return entry

    def info(self, event: str, **fields: Any) -> dict[str, Any]:
        return self._write("INFO", event, **fields)

    def warning(self, event: str, **fields: Any) -> dict[str, Any]:
        return self._write("WARNING", event, **fields)

    def error(self, event: str, **fields: Any) -> dict[str, Any]:
        return self._write("ERROR", event, **fields)

    def debug(self, event: str, **fields: Any) -> dict[str, Any]:
        return self._write("DEBUG", event, **fields)


def init_logger(config: ForgeConfig) -> ForgeLogger:
    """Initialize logger from FORGE configuration."""
    log_dir = Path(config.logging.directory)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"forge_{timestamp}.jsonl"
    return ForgeLogger(log_path=log_path, level=config.logging.level)

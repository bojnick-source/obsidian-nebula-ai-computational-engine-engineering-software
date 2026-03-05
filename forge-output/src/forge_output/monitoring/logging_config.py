"""structlog configuration for FORGE structured logging."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import structlog


def configure_structlog(
    log_level: str = "INFO",
    jsonl_path: Path | None = None,
    pretty_console: bool = False,
) -> None:
    """Configure structlog with FORGE-standard processors.

    If jsonl_path is provided, JSONL output goes to that file.
    If pretty_console=True (dev mode), use colorful ConsoleRenderer instead.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if pretty_console:
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to feed into structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[*shared_processors, renderer],
    )

    handlers: list[logging.Handler] = []

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    handlers.append(stderr_handler)

    if jsonl_path is not None:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(jsonl_path), encoding="utf-8")
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processors=[*shared_processors, structlog.processors.JSONRenderer()],
            )
        )
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for h in handlers:
        root_logger.addHandler(h)
    root_logger.setLevel(log_level.upper())


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)

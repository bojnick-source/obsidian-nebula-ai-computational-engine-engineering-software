"""
forge_agent/mcp_wrappers/_envelope.py

Shared envelope factory for MCP Wrapper Contract v1 responses.
(docs/contracts/mcp-wrapper-envelope.md)

All MCP wrapper servers import from here instead of copy-pasting.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def success_envelope(
    tool_id: str,
    wrapper_version: str,
    trace_id: str,
    invocation_id: str,
    output: dict,
    duration_ms: float,
    stdout_hash: str = "",
    stderr_lines: int = 0,
    exit_code: int = 0,
) -> dict:
    return {
        "$schema": "forge/mcp/response/v1",
        "tool_id": tool_id,
        "wrapper_version": wrapper_version,
        "trace_id": trace_id,
        "invocation_id": invocation_id,
        "timestamp": now_iso(),
        "duration_ms": int(duration_ms),
        "status": "success",
        "error_code": None,
        "error_detail": None,
        "output": output,
        "metadata": {
            "stdout_hash": stdout_hash,
            "stderr_lines": stderr_lines,
            "exit_code": exit_code,
        },
    }


def error_envelope(
    tool_id: str,
    wrapper_version: str,
    trace_id: str,
    invocation_id: str,
    error_code: str,
    error_detail: str,
    duration_ms: float,
    status: str = "error",
    exit_code: int = -1,
) -> dict:
    return {
        "$schema": "forge/mcp/response/v1",
        "tool_id": tool_id,
        "wrapper_version": wrapper_version,
        "trace_id": trace_id,
        "invocation_id": invocation_id,
        "timestamp": now_iso(),
        "duration_ms": int(duration_ms),
        "status": status,
        "error_code": error_code,
        "error_detail": error_detail,
        "output": None,
        "metadata": {"stdout_hash": "", "stderr_lines": 0, "exit_code": exit_code},
    }

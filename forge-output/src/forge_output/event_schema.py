"""Pydantic models for FORGE event stream (v1).

Mirrors the ForgeEvent C++ struct defined in
docs/architecture/v3/event-bus.md.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    RUN_START = "run_start"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    AGENT_DISPATCH = "agent_dispatch"
    TOKEN = "token"
    PROGRESS = "progress"
    BLACKBOARD_WRITE = "blackboard_write"
    VERIFICATION_GATE = "verification_gate"
    DEBATE_ROUND = "debate_round"
    TOOL_START = "tool_start"
    TOOL_COMPLETE = "tool_complete"
    VAULT_WRITE = "vault_write"
    AMNESIA_CHECK = "amnesia_check"
    DEGRADED_MODE = "degraded_mode"
    RUN_COMPLETE = "run_complete"
    ERROR = "error"


class ForgeEvent(BaseModel):
    """Single event on the FORGE event bus."""

    # Identity
    ts: datetime = Field(description="ISO-8601 UTC timestamp")
    run_id: str = Field(description="UUID v4 run identifier")
    trace_id: str = Field(description="UUID v4 trace identifier")

    # Location
    step: int = Field(default=0, description="Loop iteration (0-based)")
    phase: str = Field(default="", description="Current pipeline phase name")
    agent: str = Field(default="", description="Agent identifier emitting event")
    tool: str = Field(default="", description="Tool ID (tool events only)")
    invocation_id: str = Field(default="", description="UUID v4 invocation ID")

    # Type
    event_type: EventType

    # Progress / telemetry
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    tokens_in: int = Field(default=0, ge=0)
    tokens_out: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    provider: str = Field(default="")
    model: str = Field(default="")

    # Error
    error_code: str = Field(default="")

    # Arbitrary JSON payload (tool results, gate outcomes, etc.)
    meta: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ForgeEvent":
        # Rename meta_json → meta for wire compat
        if "meta_json" in data and "meta" not in data:
            data = {**data, "meta": data.pop("meta_json")}
        return cls.model_validate(data)

"""FORGE Data Contracts (Component F).

Pydantic models for:
  - Agent output envelopes
  - Tool response envelopes
  - Trace records
  - Blackboard slot schemas

These contracts enforce consistency across every component boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AnalysisOutput(BaseModel):
    """The 11-field output contract (FORGE_CATALOG §7.1).

    Every engineering analysis must populate all fields before
    structural verification can pass.
    """

    analysis_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    query: str
    methodology: str
    assumptions: list[str] = Field(default_factory=list)
    results: dict[str, Any] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    confidence: float = 0.0
    verification_status: str = "pending"
    sources: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class ToolResponse(BaseModel):
    """Envelope returned by every tool wrapper."""

    tool_id: str
    success: bool = False
    output: dict[str, Any] = Field(default_factory=dict)
    exit_code: int | None = None
    error: str | None = None


class TraceRecord(BaseModel):
    """A single trace entry linking an agent action to its context."""

    trace_id: str
    agent_id: str
    step: int
    event: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    payload: dict[str, Any] = Field(default_factory=dict)

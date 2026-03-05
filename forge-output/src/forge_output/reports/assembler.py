"""ReportAssembler — collects run data from events into ReportData."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from forge_output.event_schema import EventType, ForgeEvent


@dataclass
class VerificationGateResult:
    gate: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentFinding:
    agent_id: str
    phase: str
    findings: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    what_would_falsify: str = ""


@dataclass
class ToolResult:
    tool_id: str
    invocation_id: str
    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    duration_s: float = 0.0


@dataclass
class ReportData:
    run_id: str
    trace_id: str
    project: str
    task_description: str
    started_at: datetime
    completed_at: datetime | None = None
    phases_completed: list[str] = field(default_factory=list)
    agent_findings: list[AgentFinding] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    verification_gates: list[VerificationGateResult] = field(default_factory=list)
    debate_rounds: list[dict[str, Any]] = field(default_factory=list)
    vault_notes_written: list[str] = field(default_factory=list)
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    degraded_modes_activated: list[str] = field(default_factory=list)
    overall_success: bool = False


class ReportAssembler:
    """Accumulate ForgeEvents and produce a ReportData at run_complete."""

    def __init__(self) -> None:
        self._data: ReportData | None = None
        self._tool_start_times: dict[str, datetime] = {}

    def ingest(self, event: ForgeEvent) -> ReportData | None:
        """Process one event. Returns ReportData when run is complete."""
        match event.event_type:
            case EventType.RUN_START:
                self._data = ReportData(
                    run_id=event.run_id,
                    trace_id=event.trace_id,
                    project=event.meta.get("project", "unknown"),
                    task_description=event.meta.get("task_description", ""),
                    started_at=event.ts,
                )
            case EventType.PHASE_END:
                if self._data:
                    self._data.phases_completed.append(event.phase)
            case EventType.AGENT_DISPATCH:
                if self._data:
                    self._data.agent_findings.append(
                        AgentFinding(
                            agent_id=event.agent,
                            phase=event.phase,
                            findings=event.meta.get("findings", []),
                            assumptions=event.meta.get("assumptions", []),
                            confidence=event.confidence,
                            what_would_falsify=event.meta.get("what_would_falsify", ""),
                        )
                    )
                    self._data.total_tokens_in += event.tokens_in
                    self._data.total_tokens_out += event.tokens_out
                    self._data.total_cost_usd += event.cost_usd
            case EventType.TOOL_START:
                self._tool_start_times[event.invocation_id] = event.ts
            case EventType.TOOL_COMPLETE:
                if self._data:
                    started = self._tool_start_times.pop(event.invocation_id, event.ts)
                    duration = (event.ts - started).total_seconds()
                    self._data.tool_results.append(
                        ToolResult(
                            tool_id=event.tool,
                            invocation_id=event.invocation_id,
                            success=event.meta.get("success", True),
                            outputs=event.meta.get("outputs", {}),
                            duration_s=duration,
                        )
                    )
            case EventType.VERIFICATION_GATE:
                if self._data:
                    self._data.verification_gates.append(
                        VerificationGateResult(
                            gate=event.meta.get("gate", ""),
                            passed=event.meta.get("passed", True),
                            details=event.meta,
                        )
                    )
            case EventType.DEBATE_ROUND:
                if self._data:
                    self._data.debate_rounds.append(event.meta)
            case EventType.VAULT_WRITE:
                if self._data:
                    note_id = event.meta.get("note_id", "")
                    if note_id:
                        self._data.vault_notes_written.append(note_id)
            case EventType.DEGRADED_MODE:
                if self._data:
                    mode = event.meta.get("mode", "")
                    if mode:
                        self._data.degraded_modes_activated.append(mode)
            case EventType.RUN_COMPLETE:
                if self._data:
                    self._data.completed_at = event.ts
                    self._data.overall_success = event.meta.get("success", True)
                    return self._data
        return None

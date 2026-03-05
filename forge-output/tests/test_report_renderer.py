"""Tests for ReportAssembler and ReportRenderer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from forge_output.event_schema import EventType, ForgeEvent
from forge_output.reports.assembler import ReportAssembler


def _evt(**kwargs) -> ForgeEvent:
    base = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": "run-test-001",
        "trace_id": "00000000-0000-4000-8000-000000000001",
        "event_type": "run_start",
    }
    base.update(kwargs)
    return ForgeEvent.from_dict(base)


def test_assembler_full_run():
    asm = ReportAssembler()

    events = [
        _evt(event_type="run_start", meta={"project": "Aladdin-3B", "task_description": "Motor mount FEA"}),
        _evt(event_type="phase_start", phase="specialist"),
        _evt(event_type="agent_dispatch", agent="me_specialist", phase="specialist",
             confidence=0.9, tokens_in=1000, tokens_out=500, cost_usd=0.012,
             meta={"findings": ["Max stress 45 MPa"], "assumptions": ["Linear elastic"]}),
        _evt(event_type="phase_end", phase="specialist"),
        _evt(event_type="verification_gate", meta={"gate": "contract", "passed": True}),
        _evt(event_type="verification_gate", meta={"gate": "unit", "passed": True}),
        _evt(event_type="run_complete", meta={"success": True}),
    ]

    result = None
    for e in events:
        result = asm.ingest(e)

    assert result is not None
    assert result.project == "Aladdin-3B"
    assert result.overall_success is True
    assert len(result.agent_findings) == 1
    assert result.agent_findings[0].agent_id == "me_specialist"
    assert len(result.verification_gates) == 2
    assert all(g.passed for g in result.verification_gates)
    assert result.total_cost_usd == pytest.approx(0.012)


def test_assembler_no_run_complete():
    """Assembler returns None until run_complete received."""
    asm = ReportAssembler()
    result = asm.ingest(_evt(event_type="run_start"))
    assert result is None


def test_assembler_degraded_mode():
    asm = ReportAssembler()
    asm.ingest(_evt(event_type="run_start", meta={"project": "test"}))
    asm.ingest(_evt(event_type="degraded_mode", meta={"mode": "DEGRADED_SOLVER"}))
    result = asm.ingest(_evt(event_type="run_complete", meta={"success": False}))
    assert result is not None
    assert "DEGRADED_SOLVER" in result.degraded_modes_activated

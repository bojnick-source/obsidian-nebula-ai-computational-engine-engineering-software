"""
forge_agent/tests/test_log_completeness.py

Log completeness audit — verify JSONL event schema for all pipeline runs.

Every JSONL event must carry: event, phase, trace_id, timestamp.
Every phase_end event must carry duration_ms (numeric, ≥ 0).
All 9 PHASE_NAMES must have both start and end events.
All events must share the same trace_id as the TaskResult.
"""
from __future__ import annotations

import pytest

from forge_agent.core.pipeline import PHASE_NAMES, PipelineRunner, TaskRequest
from forge_agent.memory.obsidian_manager import ObsidianVaultManager

# phase_start events carry: event, phase, trace_id, timestamp
REQUIRED_START_KEYS = {"event", "phase", "trace_id", "timestamp"}
# phase_end events carry: event, phase, trace_id, status, duration_ms (no timestamp)
REQUIRED_END_KEYS = {"event", "phase", "trace_id", "status", "duration_ms"}
# All events must carry at minimum these keys
REQUIRED_ALL_KEYS = {"event", "phase", "trace_id"}


class _MinimalMockToolExecutor:
    """Minimal mock — returns success status dicts with required envelope fields."""

    def run_gmsh(self, trace_id, task_id, invocation_id, **kwargs):
        return {
            "$schema": "forge/mcp/response/v1",
            "tool_id": "gmsh",
            "wrapper_version": "1.0.0",
            "status": "success",
            "trace_id": trace_id,
            "invocation_id": invocation_id,
            "output": {"output_file": "/tmp/test.msh", "element_count": 1200},
            "duration_ms": 10,
            "error_code": None,
        }

    def run_calculix(self, trace_id, task_id, invocation_id, **kwargs):
        return {
            "$schema": "forge/mcp/response/v1",
            "tool_id": "calculix",
            "wrapper_version": "1.0.0",
            "status": "success",
            "trace_id": trace_id,
            "invocation_id": invocation_id,
            "output": {"frd_file": "/tmp/test.frd", "max_von_mises_mpa": 110.5},
            "duration_ms": 50,
            "error_code": None,
        }


@pytest.fixture()
def pipeline_events(tmp_path):
    """Run a full pipeline and return (result, events)."""
    vault = ObsidianVaultManager(vault_path=tmp_path)
    runner = PipelineRunner(
        config={"provider": "anthropic"},
        tool_executor=_MinimalMockToolExecutor(),
        vault_manager=vault,
        anthropic_client=None,  # uses _stub_specialist() — offline, no API call
    )
    request = TaskRequest(
        task_type="engineering_full",
        project="log-audit",
        component="test-component",
        description="Log completeness audit test run.",
        load_cases=[],
    )
    result = runner.run(request)
    return result, runner._jsonl_events


def test_every_event_has_required_keys(pipeline_events):
    """
    Every JSONL event must carry: event, phase, trace_id.
    phase_start events additionally carry: timestamp.
    phase_end events additionally carry: status, duration_ms.
    """
    result, events = pipeline_events
    assert events, "No JSONL events emitted"
    for event in events:
        # All events must have the base keys
        missing_base = REQUIRED_ALL_KEYS - set(event.keys())
        assert not missing_base, (
            f"Event missing base required keys {missing_base}: {event}"
        )
        # phase_start must have timestamp
        if event.get("event") == "phase_start":
            missing_start = REQUIRED_START_KEYS - set(event.keys())
            assert not missing_start, (
                f"phase_start event missing keys {missing_start}: {event}"
            )
        # phase_end must have status and duration_ms
        elif event.get("event") == "phase_end":
            missing_end = REQUIRED_END_KEYS - set(event.keys())
            assert not missing_end, (
                f"phase_end event missing keys {missing_end}: {event}"
            )


def test_phase_end_has_duration_ms(pipeline_events):
    """Every phase_end event must have duration_ms as a numeric value."""
    result, events = pipeline_events
    end_events = [e for e in events if e.get("event") == "phase_end"]
    assert end_events, "No phase_end events found"
    for event in end_events:
        assert "duration_ms" in event, (
            f"phase_end event for phase={event.get('phase')!r} missing duration_ms"
        )
        assert isinstance(event["duration_ms"], (int, float)), (
            f"duration_ms must be numeric, got {type(event['duration_ms'])!r} "
            f"in phase={event.get('phase')!r}"
        )


def test_duration_ms_is_non_negative(pipeline_events):
    """All duration_ms values in phase_end events must be ≥ 0."""
    result, events = pipeline_events
    end_events = [e for e in events if e.get("event") == "phase_end"]
    for event in end_events:
        dm = event.get("duration_ms", 0)
        assert dm >= 0, (
            f"duration_ms must be ≥ 0, got {dm} in phase={event.get('phase')!r}"
        )


def test_all_9_phases_have_start_and_end(pipeline_events):
    """Every phase in PHASE_NAMES must emit both phase_start and phase_end events."""
    result, events = pipeline_events
    start_phases = {e["phase"] for e in events if e.get("event") == "phase_start"}
    end_phases = {e["phase"] for e in events if e.get("event") == "phase_end"}
    expected = set(PHASE_NAMES)

    missing_start = expected - start_phases
    missing_end = expected - end_phases
    assert not missing_start, f"Missing phase_start for phases: {missing_start}"
    assert not missing_end, f"Missing phase_end for phases: {missing_end}"


def test_trace_id_consistent_across_all_events(pipeline_events):
    """All JSONL events must share the same trace_id as result.trace_id."""
    result, events = pipeline_events
    assert result.trace_id, "result.trace_id must not be empty"
    for event in events:
        assert event.get("trace_id") == result.trace_id, (
            f"Event trace_id mismatch in phase={event.get('phase')!r}: "
            f"{event.get('trace_id')!r} != {result.trace_id!r}"
        )

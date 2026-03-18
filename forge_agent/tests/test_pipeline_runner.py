"""Tests for forge_agent/core/pipeline.py — 9-phase FORGE pipeline runner."""

from __future__ import annotations

from unittest.mock import MagicMock

from forge_agent.core.pipeline import (
    PipelineRunner,
    TaskRequest,
    TaskResult,
    VALID_SPECIALIST_OUTPUT,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(**kwargs) -> TaskRequest:
    defaults = dict(
        task_type="structural_analysis",
        project="phoenix",
        component="bracket",
        description="Stress analysis of aluminium bracket under 5 kN axial load",
        load_cases=["axial_5kN"],
    )
    defaults.update(kwargs)
    return TaskRequest(**defaults)


def _make_tool_executor(status: str = "ok") -> MagicMock:
    """Return a mock tool executor whose run_gmsh / run_calculix return given status."""
    exe = MagicMock()
    exe.run_gmsh.return_value = {"tool": "gmsh", "status": status, "trace_id": ""}
    exe.run_calculix.return_value = {"tool": "calculix", "status": status, "trace_id": ""}
    return exe


def _make_vault_manager(amnesia_ok: bool = True) -> MagicMock:
    vm = MagicMock()
    vm.upsert_note.return_value = "engineering/phoenix/bracket-test.md"
    vm.amnesia_check.return_value = amnesia_ok
    vm.search_notes.return_value = []
    return vm


def _make_anthropic_client() -> MagicMock:
    """Return a mock Anthropic client whose messages.create returns stub-compliant JSON."""
    import json

    client = MagicMock()
    content_block = MagicMock()
    content_block.text = json.dumps(VALID_SPECIALIST_OUTPUT)
    message = MagicMock()
    message.content = [content_block]
    client.messages.create.return_value = message
    return client


# ---------------------------------------------------------------------------
# Test 1 — trace_id propagated through all phases
# ---------------------------------------------------------------------------


def test_trace_id_propagated_through_all_phases():
    """The same trace_id must appear in result, all JSONL events, and vault write path."""
    vm = _make_vault_manager()
    runner = PipelineRunner(
        config={"provider": "anthropic"},
        tool_executor=_make_tool_executor(),
        vault_manager=vm,
        anthropic_client=None,  # use stub
    )
    result = runner.run(_make_request())

    trace_id = result.trace_id
    assert trace_id, "trace_id must not be empty"

    # Every JSONL event must carry the same trace_id
    for event in runner._jsonl_events:
        assert event["trace_id"] == trace_id, (
            f"Event '{event['event']}' phase='{event['phase']}' "
            f"has trace_id={event['trace_id']!r}, expected {trace_id!r}"
        )

    # vault write path must contain the trace_id prefix (first 8 chars)
    trace_prefix = trace_id[:8]
    upsert_calls = vm.upsert_note.call_args_list
    assert upsert_calls, "upsert_note should have been called"
    note_path_arg = upsert_calls[0][0][0]  # first positional arg of first call
    assert trace_prefix in note_path_arg, (
        f"Vault note path {note_path_arg!r} does not contain trace prefix {trace_prefix!r}"
    )

    # amnesia_check must be called with the same path
    amnesia_calls = vm.amnesia_check.call_args_list
    assert amnesia_calls, "amnesia_check should have been called"
    assert amnesia_calls[0][0][0] == note_path_arg


# ---------------------------------------------------------------------------
# Test 2 — verification failure blocks vault write
# ---------------------------------------------------------------------------


def test_verification_failure_blocks_vault_write():
    """If specialist output is missing required fields, vault write must NOT be called."""
    vm = _make_vault_manager()
    exe = _make_tool_executor()

    # Build a mock anthropic client that returns output missing the 'equations' field
    import json
    invalid_output = dict(VALID_SPECIALIST_OUTPUT)
    del invalid_output["equations"]

    client = MagicMock()
    content_block = MagicMock()
    content_block.text = json.dumps(invalid_output)
    message = MagicMock()
    message.content = [content_block]
    client.messages.create.return_value = message

    runner = PipelineRunner(
        config={"provider": "anthropic"},
        tool_executor=exe,
        vault_manager=vm,
        anthropic_client=client,
    )
    result = runner.run(_make_request())

    # Vault write must NOT have been called
    vm.upsert_note.assert_not_called()
    # Result status must be "failed"
    assert result.status == "failed", f"Expected 'failed', got {result.status!r}"


# ---------------------------------------------------------------------------
# Test 3 — happy path returns complete (or degraded if tools absent)
# ---------------------------------------------------------------------------


def test_pipeline_returns_complete_on_happy_path():
    """Full mock run with stub specialist must return status in {'complete', 'degraded'}."""
    vm = _make_vault_manager()
    exe = _make_tool_executor(status="ok")

    runner = PipelineRunner(
        config={"provider": "anthropic"},
        tool_executor=exe,
        vault_manager=vm,
        anthropic_client=None,  # stub
    )
    result = runner.run(_make_request())

    assert isinstance(result, TaskResult)
    assert result.status in {"complete", "degraded"}, (
        f"Unexpected status: {result.status!r}"
    )
    assert result.trace_id
    assert result.result_summary


# ---------------------------------------------------------------------------
# Test 4 — JSONL events: 9 start + 9 end, all with trace_id
# ---------------------------------------------------------------------------


def test_jsonl_has_9_phase_start_and_end_events():
    """Pipeline must emit exactly 9 phase_start and 9 phase_end events, all with trace_id."""
    vm = _make_vault_manager()
    runner = PipelineRunner(
        config={"provider": "anthropic"},
        tool_executor=_make_tool_executor(),
        vault_manager=vm,
        anthropic_client=None,  # stub
    )
    result = runner.run(_make_request())

    start_events = [e for e in runner._jsonl_events if e["event"] == "phase_start"]
    end_events = [e for e in runner._jsonl_events if e["event"] == "phase_end"]

    assert len(start_events) == 9, (
        f"Expected 9 phase_start events, got {len(start_events)}. "
        f"Phases seen: {[e['phase'] for e in start_events]}"
    )
    assert len(end_events) == 9, (
        f"Expected 9 phase_end events, got {len(end_events)}. "
        f"Phases seen: {[e['phase'] for e in end_events]}"
    )

    trace_id = result.trace_id
    for event in runner._jsonl_events:
        assert "trace_id" in event, f"Event missing trace_id: {event}"
        assert event["trace_id"] == trace_id, (
            f"Event trace_id mismatch: {event['trace_id']!r} != {trace_id!r}"
        )

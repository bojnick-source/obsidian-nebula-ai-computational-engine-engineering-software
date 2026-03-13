"""Tests for forge_manufacturing.model — Pydantic data models."""

from __future__ import annotations

import pytest

from forge_manufacturing.model import (
    BlockLevel,
    BuildLedger,
    ProcessStep,
    Spec,
    StepType,
    block_gte,
    block_index,
)


# ── BlockLevel helpers ────────────────────────────────────────────────────────


def test_block_index_order():
    assert block_index(BlockLevel.BLOCK_0) == 0
    assert block_index(BlockLevel.BLOCK_4) == 4


def test_block_gte_true():
    assert block_gte(BlockLevel.BLOCK_2, BlockLevel.BLOCK_1)
    assert block_gte(BlockLevel.BLOCK_0, BlockLevel.BLOCK_0)


def test_block_gte_false():
    assert not block_gte(BlockLevel.BLOCK_1, BlockLevel.BLOCK_2)


# ── ProcessStep ───────────────────────────────────────────────────────────────


def test_process_step_defaults():
    step = ProcessStep(step_id="TEST-001", step_type=StepType.GATE)
    assert step.prerequisites == []
    assert step.acceptance_criteria == []
    assert step.required_evidence == []


def test_process_step_extra_field_rejected():
    with pytest.raises(Exception):
        ProcessStep(
            step_id="TEST",
            step_type=StepType.GATE,
            unknown_field="should fail",  # type: ignore[call-arg]
        )


# ── Spec ─────────────────────────────────────────────────────────────────────


def _make_minimal_spec() -> dict:
    return {
        "meta": {
            "program_name": "Test Program",
            "owner": "Test Owner",
            "scope": "Test scope",
        }
    }


def test_spec_loads_minimal():
    spec = Spec.model_validate(_make_minimal_spec())
    assert spec.meta.program_name == "Test Program"
    assert spec.process_flow == []


def test_spec_steps_for_block_all_applicable():
    """Steps with no WhenCondition should all be included."""
    data = _make_minimal_spec()
    data["process_flow"] = [
        {"step_id": "S1", "step_type": "gate"},
        {"step_id": "S2", "step_type": "process"},
    ]
    spec = Spec.model_validate(data)
    steps = spec.steps_for_block(BlockLevel.BLOCK_0)
    assert len(steps) == 2


def test_spec_steps_for_block_filtered():
    """Steps with block_level_gte=BLOCK_2 should be excluded at BLOCK_0."""
    data = _make_minimal_spec()
    data["process_flow"] = [
        {"step_id": "S1", "step_type": "gate"},
        {
            "step_id": "S2",
            "step_type": "process",
            "when": {"block_level_gte": "BLOCK_2"},
        },
    ]
    spec = Spec.model_validate(data)
    steps_b0 = spec.steps_for_block(BlockLevel.BLOCK_0)
    steps_b2 = spec.steps_for_block(BlockLevel.BLOCK_2)
    assert len(steps_b0) == 1
    assert len(steps_b2) == 2


# ── BuildLedger ───────────────────────────────────────────────────────────────


def test_build_ledger_creates():
    ledger = BuildLedger(
        build_id="BLD-001",
        spec_hash="abc123",
        started_utc="2026-01-01T00:00:00+00:00",
    )
    assert ledger.build_id == "BLD-001"
    assert ledger.final_disposition is None
    assert ledger.steps == []

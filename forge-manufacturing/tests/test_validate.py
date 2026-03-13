"""Tests for forge_manufacturing.validate — topological sort and spec loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge_manufacturing.model import ProcessStep, StepType
from forge_manufacturing.validate import (
    SpecValidationError,
    _ensure_prerequisites_exist,
    _ensure_unique_step_ids,
    load_spec,
    topological_sort,
    validate_spec,
)

# ── Path to shipped YAML specs ────────────────────────────────────────────────
_SPECS_DIR = Path(__file__).parent.parent / "specs"


# ── _ensure_unique_step_ids ───────────────────────────────────────────────────


def test_unique_ids_ok():
    steps = [
        ProcessStep(step_id="A", step_type=StepType.PROCESS),
        ProcessStep(step_id="B", step_type=StepType.GATE),
    ]
    _ensure_unique_step_ids(steps)  # Should not raise


def test_duplicate_ids_raises():
    steps = [
        ProcessStep(step_id="A", step_type=StepType.PROCESS),
        ProcessStep(step_id="A", step_type=StepType.GATE),
    ]
    with pytest.raises(SpecValidationError, match="Duplicate"):
        _ensure_unique_step_ids(steps)


# ── _ensure_prerequisites_exist ──────────────────────────────────────────────


def test_prerequisites_ok():
    steps = [
        ProcessStep(step_id="A", step_type=StepType.PROCESS),
        ProcessStep(step_id="B", step_type=StepType.GATE, prerequisites=["A"]),
    ]
    _ensure_prerequisites_exist(steps)  # Should not raise


def test_missing_prereq_raises():
    steps = [
        ProcessStep(step_id="B", step_type=StepType.GATE, prerequisites=["MISSING"]),
    ]
    with pytest.raises(SpecValidationError, match="undefined prerequisites"):
        _ensure_prerequisites_exist(steps)


# ── topological_sort ─────────────────────────────────────────────────────────


def _make_chain(n: int) -> list[ProcessStep]:
    """Create a linear chain A→B→C→... of length n."""
    steps = [ProcessStep(step_id="S0", step_type=StepType.PROCESS)]
    for i in range(1, n):
        steps.append(ProcessStep(
            step_id=f"S{i}",
            step_type=StepType.PROCESS,
            prerequisites=[f"S{i - 1}"],
        ))
    return steps


def test_topo_sort_linear_chain():
    steps = _make_chain(5)
    sorted_steps = topological_sort(steps)
    ids = [s.step_id for s in sorted_steps]
    assert ids == ["S0", "S1", "S2", "S3", "S4"]


def test_topo_sort_parallel():
    """Two independent branches should both appear after the common root."""
    steps = [
        ProcessStep(step_id="ROOT", step_type=StepType.PROCESS),
        ProcessStep(step_id="BRANCH_A", step_type=StepType.PROCESS, prerequisites=["ROOT"]),
        ProcessStep(step_id="BRANCH_B", step_type=StepType.PROCESS, prerequisites=["ROOT"]),
    ]
    sorted_steps = topological_sort(steps)
    ids = [s.step_id for s in sorted_steps]
    assert ids[0] == "ROOT"
    assert set(ids[1:]) == {"BRANCH_A", "BRANCH_B"}


def test_topo_sort_cycle_raises():
    steps = [
        ProcessStep(step_id="A", step_type=StepType.PROCESS, prerequisites=["B"]),
        ProcessStep(step_id="B", step_type=StepType.PROCESS, prerequisites=["A"]),
    ]
    with pytest.raises(SpecValidationError, match="cycle"):
        topological_sort(steps)


def test_topo_sort_empty():
    assert topological_sort([]) == []


# ── load_spec: shipped YAML files ─────────────────────────────────────────────


@pytest.mark.parametrize("filename", [
    "sfcs_drone_mdp_v0.yaml",
    "am_mdp_v0.yaml",
])
def test_load_spec_shipped(filename: str):
    """The shipped manufacturing specs must load and validate without errors."""
    spec_path = _SPECS_DIR / filename
    if not spec_path.exists():
        pytest.skip(f"Spec not found: {spec_path}")
    spec = load_spec(spec_path)
    assert spec.meta is not None
    assert len(spec.process_flow) > 0


def test_load_spec_validates_process_flow():
    """The SFCS drone spec process flow must be topologically sortable."""
    spec_path = _SPECS_DIR / "sfcs_drone_mdp_v0.yaml"
    if not spec_path.exists():
        pytest.skip("sfcs_drone_mdp_v0.yaml not found")
    spec = load_spec(spec_path)
    validate_spec(spec)  # Must not raise


def test_load_spec_empty_raises(tmp_path: Path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    with pytest.raises(SpecValidationError, match="empty"):
        load_spec(empty)

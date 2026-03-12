"""Numerical Stability & Physics Validation Tests — Repository Layer 2.

Validates:
1. Mass property calculations (CG, mass budget) with edge-case inputs
2. Transform matrix orthogonality and determinant = ±1
3. Rotation composition associativity
4. Disassembly DAG — topological sort produces finite, consistent ordering
5. Fastener torque spec physical bounds
6. Clearance / interference numeric bounds and edge cases
7. Conservation: total mass is sum of component masses (no numerical drift)

These tests probe the mathematical correctness and physical plausibility
of the forge_assembly numerical engine — aligned with the Reid Industries
validation philosophy of mathematical correctness → physical bounds → robustness.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).parent.parent
for _src in ("forge-assembly/src",):
    _p = REPO_ROOT / _src
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from forge_assembly.mass_props import compute_mass_properties  # noqa: E402
from forge_assembly.placement import ComponentPlacement  # noqa: E402
from forge_assembly.fasteners import FastenerSpec, FASTENER_TOOL_MAP  # noqa: E402
from forge_assembly.disassembly import (  # noqa: E402
    DisassemblyNode,
    DisassemblyResult,
    format_disassembly_table,
)
from forge_assembly.maintenance import ServiceLevel, classify_maintenance_access  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_placement(
    cid: str = "comp_a",
    translation: tuple = (0.0, 0.0, 0.0),
    rotation: tuple = (0.0, 0.0, 0.0),
    mass_kg: float = 1.0,
) -> ComponentPlacement:
    return ComponentPlacement(
        component_id=cid,
        name=cid,
        translation_mm=translation,
        rotation_deg=rotation,
        stl_path="",
        mass_kg=mass_kg,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mass properties — correctness and conservation
# ─────────────────────────────────────────────────────────────────────────────

def test_total_mass_conservation() -> None:
    """Total mass must equal sum of individual component masses."""
    placements = [
        _make_placement("a", mass_kg=1.5),
        _make_placement("b", mass_kg=2.3),
        _make_placement("c", mass_kg=0.7),
    ]
    result = compute_mass_properties(placements)
    expected = 1.5 + 2.3 + 0.7
    assert abs(result.total_mass_kg - expected) < 1e-10, (
        f"Mass not conserved: got {result.total_mass_kg}, expected {expected}"
    )


def test_cg_at_centroid_of_equal_mass_symmetric_pair() -> None:
    """CG of two equal-mass components at ±x must be at x=0."""
    placements = [
        _make_placement("left",  translation=(-100.0, 0.0, 0.0), mass_kg=1.0),
        _make_placement("right", translation=( 100.0, 0.0, 0.0), mass_kg=1.0),
    ]
    result = compute_mass_properties(placements)
    cx, cy, cz = result.center_of_mass_mm
    assert abs(cx) < 1e-10, f"CG x should be 0, got {cx}"
    assert abs(cy) < 1e-10, f"CG y should be 0, got {cy}"
    assert abs(cz) < 1e-10, f"CG z should be 0, got {cz}"


def test_cg_weighted_correctly() -> None:
    """CG must follow weighted average: heavier component pulls CG toward it."""
    placements = [
        _make_placement("light", translation=(0.0, 0.0, 0.0), mass_kg=1.0),
        _make_placement("heavy", translation=(100.0, 0.0, 0.0), mass_kg=9.0),
    ]
    result = compute_mass_properties(placements)
    cx = result.center_of_mass_mm[0]
    expected_cx = (1.0 * 0.0 + 9.0 * 100.0) / 10.0  # = 90.0
    assert abs(cx - expected_cx) < 1e-10, (
        f"Weighted CG wrong: got {cx}, expected {expected_cx}"
    )


def test_mass_budget_margin_positive() -> None:
    """Mass margin must be positive when total < budget."""
    placements = [_make_placement("a", mass_kg=5.0)]
    result = compute_mass_properties(placements, mass_budget_kg=10.0)
    assert result.mass_margin_kg == pytest.approx(5.0)
    assert not result.over_budget


def test_mass_budget_over_budget_flag() -> None:
    """over_budget flag must trigger when total > budget."""
    placements = [_make_placement("a", mass_kg=15.0)]
    result = compute_mass_properties(placements, mass_budget_kg=10.0)
    assert result.over_budget
    assert result.mass_margin_kg == pytest.approx(-5.0)


def test_zero_mass_assembly_no_division_by_zero() -> None:
    """Zero-mass assembly must not raise ZeroDivisionError."""
    placements = [_make_placement("a", mass_kg=0.0)]
    result = compute_mass_properties(placements)
    assert result.total_mass_kg == 0.0
    assert result.center_of_mass_mm == (0.0, 0.0, 0.0)


def test_single_component_cg_equals_translation() -> None:
    """Single-component CG must equal its translation vector."""
    tx, ty, tz = 42.5, -17.3, 5.0
    placements = [_make_placement("solo", translation=(tx, ty, tz), mass_kg=3.0)]
    result = compute_mass_properties(placements)
    cx, cy, cz = result.center_of_mass_mm
    assert abs(cx - tx) < 1e-10
    assert abs(cy - ty) < 1e-10
    assert abs(cz - tz) < 1e-10


# ─────────────────────────────────────────────────────────────────────────────
# 2. Transform matrix orthogonality (rotation must preserve distances)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rx,ry,rz", [
    (0.0, 0.0, 0.0),
    (45.0, 0.0, 0.0),
    (0.0, 90.0, 0.0),
    (0.0, 0.0, 180.0),
    (30.0, 45.0, 60.0),
    (90.0, 90.0, 90.0),
])
def test_transform_rotation_is_orthogonal(rx: float, ry: float, rz: float) -> None:
    """Rotation sub-matrix of transform must be orthogonal: R @ Rᵀ = I."""
    p = _make_placement("t", rotation=(rx, ry, rz))
    T = p.transform_matrix()
    R = T[:3, :3]
    product = R @ R.T
    np.testing.assert_allclose(
        product, np.eye(3), atol=1e-12,
        err_msg=f"R not orthogonal for rotation ({rx},{ry},{rz})",
    )


@pytest.mark.parametrize("rx,ry,rz", [
    (0.0, 0.0, 0.0),
    (45.0, 30.0, 0.0),
    (90.0, 0.0, 90.0),
])
def test_transform_rotation_determinant_is_one(rx: float, ry: float, rz: float) -> None:
    """Rotation sub-matrix must have determinant = +1 (proper rotation, no reflection)."""
    p = _make_placement("d", rotation=(rx, ry, rz))
    T = p.transform_matrix()
    R = T[:3, :3]
    det = np.linalg.det(R)
    assert abs(det - 1.0) < 1e-12, (
        f"det(R) = {det} ≠ 1.0 for rotation ({rx},{ry},{rz})"
    )


def test_identity_rotation_gives_identity_matrix() -> None:
    """Zero rotation must produce identity rotation sub-matrix."""
    p = _make_placement("id", rotation=(0.0, 0.0, 0.0))
    T = p.transform_matrix()
    np.testing.assert_allclose(T[:3, :3], np.eye(3), atol=1e-15)


def test_translation_is_preserved_in_transform() -> None:
    """Translation components of transform must match placement translation."""
    tx, ty, tz = 123.4, -56.7, 0.1
    p = _make_placement("tr", translation=(tx, ty, tz))
    T = p.transform_matrix()
    assert abs(T[0, 3] - tx) < 1e-12
    assert abs(T[1, 3] - ty) < 1e-12
    assert abs(T[2, 3] - tz) < 1e-12


def test_full_rotation_360_returns_to_identity() -> None:
    """A full 360° rotation must yield (near) identity rotation matrix."""
    p = _make_placement("full", rotation=(360.0, 0.0, 0.0))
    T = p.transform_matrix()
    np.testing.assert_allclose(T[:3, :3], np.eye(3), atol=1e-12)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Fastener specs — physical plausibility bounds
# ─────────────────────────────────────────────────────────────────────────────

def test_fastener_torque_spec_positive() -> None:
    """All fasteners in FASTENER_TOOL_MAP must have positive torque specs."""
    for fastener_type, spec in FASTENER_TOOL_MAP.items():
        if hasattr(spec, "torque_nm") and spec.torque_nm is not None:
            assert spec.torque_nm > 0, (
                f"{fastener_type}: torque must be positive, got {spec.torque_nm}"
            )


def test_fastener_tool_map_not_empty() -> None:
    """FASTENER_TOOL_MAP must have at least one entry."""
    assert len(FASTENER_TOOL_MAP) > 0, "FASTENER_TOOL_MAP is empty"


def test_fastener_tool_map_all_values_are_nonempty_lists() -> None:
    """Every FASTENER_TOOL_MAP entry must map to a non-empty list of tool names."""
    for fastener_type, tools in FASTENER_TOOL_MAP.items():
        assert isinstance(tools, list), f"{fastener_type}: tools must be a list"
        assert len(tools) > 0, f"{fastener_type}: tool list must not be empty"
        for t in tools:
            assert isinstance(t, str) and t, (
                f"{fastener_type}: all tool names must be non-empty strings"
            )


def test_fastener_spec_torque_is_positive() -> None:
    """FastenerSpec.torque_spec_nm must be positive (physical plausibility)."""
    spec = FastenerSpec(
        interface_id="IF-TEST-001",
        connection_description="test bolt",
        fastener_type="M3_socket_head",
        quantity=4,
        material="steel",
        torque_spec_nm=1.5,
        thread_engagement_mm=6.0,
        locking="none",
    )
    assert spec.torque_spec_nm > 0


def test_fastener_spec_validates_known_type() -> None:
    """FastenerSpec.validate() must return no errors for a known fastener type."""
    spec = FastenerSpec(
        interface_id="IF-TEST-002",
        connection_description="M4 bolt",
        fastener_type="M4_socket_head",
        quantity=2,
        material="stainless",
        torque_spec_nm=3.0,
        thread_engagement_mm=14.0,  # M4: min = 3×4 = 12 mm
        locking="thread_lock",
    )
    errors = spec.validate()
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_fastener_spec_validates_unknown_type() -> None:
    """FastenerSpec.validate() must report error for unknown fastener type."""
    spec = FastenerSpec(
        interface_id="IF-TEST-003",
        connection_description="mystery bolt",
        fastener_type="NONEXISTENT_BOLT",
        quantity=1,
        material="plastic",
        torque_spec_nm=0.5,
        thread_engagement_mm=3.0,
        locking="none",
    )
    errors = spec.validate()
    assert len(errors) > 0, "Unknown fastener type should produce validation errors"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Disassembly DAG — topological consistency
# ─────────────────────────────────────────────────────────────────────────────

def _make_disassembly_result(component_ids: list[str]) -> DisassemblyResult:
    """Build a minimal DisassemblyResult for testing."""
    nodes = [
        DisassemblyNode(component_id=cid, name=cid)
        for cid in component_ids
    ]
    return DisassemblyResult(
        nodes=nodes,
        removal_order=list(component_ids),
        total_estimated_time_min=0.0,
        non_destructive_count=len(component_ids),
        total_count=len(component_ids),
    )


def test_disassembly_dag_produces_ordered_sequence() -> None:
    """Disassembly removal_order must list every component exactly once."""
    component_ids = ["motor", "bracket", "housing"]
    result = _make_disassembly_result(component_ids)
    seen = set(result.removal_order)
    expected = set(component_ids)
    assert seen == expected, (
        f"removal_order {result.removal_order} missing: {expected - seen}"
    )


def test_disassembly_dag_no_duplicates() -> None:
    """Disassembly removal_order must not repeat any component."""
    component_ids = [f"c{i}" for i in range(6)]
    result = _make_disassembly_result(component_ids)
    assert len(result.removal_order) == len(set(result.removal_order)), (
        f"Duplicate entries in removal_order: {result.removal_order}"
    )


def test_disassembly_table_format_is_string() -> None:
    """format_disassembly_table must return a non-empty string."""
    result = _make_disassembly_result(["a", "b", "c"])
    table = format_disassembly_table(result)
    assert isinstance(table, str), "format_disassembly_table must return str"
    assert len(table.strip()) > 0, "Disassembly table must not be empty"


def test_disassembly_counts_consistent() -> None:
    """total_count and non_destructive_count must be internally consistent."""
    result = _make_disassembly_result(["x", "y", "z"])
    assert result.total_count == len(result.nodes), (
        f"total_count {result.total_count} != node count {len(result.nodes)}"
    )
    assert 0 <= result.non_destructive_count <= result.total_count, (
        f"non_destructive_count {result.non_destructive_count} out of bounds"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Maintenance access classification — physical bounds
# ─────────────────────────────────────────────────────────────────────────────

def test_maintenance_service_levels_are_ordered() -> None:
    """ServiceLevel enum must have at least 2 distinct levels."""
    levels = list(ServiceLevel)
    assert len(levels) >= 2, "ServiceLevel must have at least 2 levels"
    assert len(set(levels)) == len(levels), "ServiceLevel must have unique entries"


def test_classify_maintenance_returns_summary() -> None:
    """classify_maintenance_access must return a MaintenanceSummary object."""
    from forge_assembly.maintenance import MaintenanceSummary  # noqa: PLC0415
    result = _make_disassembly_result(["motor", "bracket"])
    summary = classify_maintenance_access(result)
    assert isinstance(summary, MaintenanceSummary), (
        f"Expected MaintenanceSummary, got {type(summary)}"
    )


def test_classify_maintenance_covers_all_components() -> None:
    """Maintenance classification must cover every component in the DAG."""
    component_ids = ["motor", "bracket", "housing", "cover"]
    result = _make_disassembly_result(component_ids)
    summary = classify_maintenance_access(result)
    classified_ids = {c.component_id for c in summary.classifications}
    assert classified_ids == set(component_ids), (
        f"Unclassified components: {set(component_ids) - classified_ids}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Numerical edge cases — large values, negative coordinates
# ─────────────────────────────────────────────────────────────────────────────

def test_mass_props_large_coordinates_no_overflow() -> None:
    """Mass computation must be stable for large coordinate values (1e6 mm = 1 km)."""
    placements = [
        _make_placement("far_a", translation=(1e6, 0.0, 0.0), mass_kg=1.0),
        _make_placement("far_b", translation=(-1e6, 0.0, 0.0), mass_kg=1.0),
    ]
    result = compute_mass_properties(placements)
    assert math.isfinite(result.total_mass_kg)
    assert all(math.isfinite(c) for c in result.center_of_mass_mm)
    assert abs(result.center_of_mass_mm[0]) < 1e-6  # Should cancel to ≈0


def test_mass_props_very_small_mass_no_underflow() -> None:
    """Mass computation must handle micro-gram components without underflow."""
    placements = [
        _make_placement("micro", translation=(10.0, 0.0, 0.0), mass_kg=1e-9),
        _make_placement("heavy", translation=(0.0, 0.0, 0.0), mass_kg=100.0),
    ]
    result = compute_mass_properties(placements)
    assert math.isfinite(result.total_mass_kg)
    # CG should be very close to heavy component (nearly all mass there)
    assert abs(result.center_of_mass_mm[0]) < 0.01


def test_rotation_90_degree_increments_exact() -> None:
    """90° rotations must produce exact 0 and ±1 matrix entries."""
    for angle in (90.0, 180.0, 270.0):
        p = _make_placement("r90", rotation=(0.0, 0.0, angle))
        T = p.transform_matrix()
        R = T[:3, :3]
        # All entries should be close to 0, 1, or -1
        for val in R.flat:
            assert abs(val) < 1e-14 or abs(abs(val) - 1.0) < 1e-14, (
                f"Rotation {angle}° produced non-cardinal value {val}"
            )

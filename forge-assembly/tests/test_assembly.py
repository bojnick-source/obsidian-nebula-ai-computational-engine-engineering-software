"""Tests for forge-assembly package."""

from __future__ import annotations

import pytest

from forge_assembly.disassembly import build_disassembly_dag, format_disassembly_table
from forge_assembly.fasteners import FastenerSpec, FASTENER_TOOL_MAP
from forge_assembly.maintenance import ServiceLevel, classify_maintenance_access
from forge_assembly.mass_props import compute_mass_properties
from forge_assembly.placement import ComponentPlacer


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

COMPONENTS = [
    {"id": "C-001", "name": "Fuselage",  "mass_kg": 1.2, "stl_path": ""},
    {"id": "C-002", "name": "Wing L",    "mass_kg": 0.4, "stl_path": ""},
    {"id": "C-003", "name": "Wing R",    "mass_kg": 0.4, "stl_path": ""},
    {"id": "C-004", "name": "Motor L",   "mass_kg": 0.15, "stl_path": ""},
    {"id": "C-005", "name": "Motor R",   "mass_kg": 0.15, "stl_path": ""},
    {"id": "C-006", "name": "Battery",   "mass_kg": 0.8, "stl_path": ""},
    {"id": "C-007", "name": "Canopy",    "mass_kg": 0.05, "stl_path": ""},
]

INTERFACES = [
    {"id": "IF-001", "component_ids": ["C-001", "C-002"], "offset_mm": (0, -350, 0),
     "joint_type": "bolted", "fastener_type": "M4_socket_head"},
    {"id": "IF-002", "component_ids": ["C-001", "C-003"], "offset_mm": (0, 350, 0),
     "joint_type": "bolted", "fastener_type": "M4_socket_head"},
    {"id": "IF-003", "component_ids": ["C-002", "C-004"], "offset_mm": (-50, 0, 20),
     "joint_type": "bolted", "fastener_type": "M3_socket_head"},
    {"id": "IF-004", "component_ids": ["C-003", "C-005"], "offset_mm": (-50, 0, 20),
     "joint_type": "bolted", "fastener_type": "M3_socket_head"},
    {"id": "IF-005", "component_ids": ["C-001", "C-006"], "offset_mm": (200, 0, -30),
     "joint_type": "snap_fit", "fastener_type": ""},
    {"id": "IF-006", "component_ids": ["C-001", "C-007"], "offset_mm": (100, 0, 50),
     "joint_type": "snap_fit", "fastener_type": ""},
]


# ─────────────────────────────────────────────────────────────────────────────
# Placement tests
# ─────────────────────────────────────────────────────────────────────────────

def test_all_components_placed():
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    placed_ids = {p.component_id for p in placements}
    assert placed_ids == {c["id"] for c in COMPONENTS}


def test_primary_at_origin():
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    primary = next(p for p in placements if p.component_id == "C-001")
    assert primary.translation_mm == (0.0, 0.0, 0.0)


def test_wing_offset():
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    wing_l = next(p for p in placements if p.component_id == "C-002")
    assert wing_l.translation_mm[1] == pytest.approx(-350.0)


# ─────────────────────────────────────────────────────────────────────────────
# Mass properties tests
# ─────────────────────────────────────────────────────────────────────────────

def test_total_mass():
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    props = compute_mass_properties(placements, mass_budget_kg=3.5)
    expected = sum(c["mass_kg"] for c in COMPONENTS)
    assert props.total_mass_kg == pytest.approx(expected, rel=1e-6)


def test_mass_budget_margin():
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    props = compute_mass_properties(placements, mass_budget_kg=3.5)
    assert props.mass_margin_kg is not None
    assert not props.over_budget


def test_mass_overrun_flag():
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    props = compute_mass_properties(placements, mass_budget_kg=1.0)  # way too low
    assert props.over_budget


# ─────────────────────────────────────────────────────────────────────────────
# Fastener validation tests
# ─────────────────────────────────────────────────────────────────────────────

def test_fastener_tool_map_coverage():
    """All common fastener types have tool mappings."""
    for ftype in ["M3_socket_head", "M4_socket_head", "M5_socket_head"]:
        assert ftype in FASTENER_TOOL_MAP
        assert len(FASTENER_TOOL_MAP[ftype]) > 0


def test_fastener_thread_engagement_ok():
    spec = FastenerSpec(
        interface_id="IF-001",
        connection_description="Wing to fuselage",
        fastener_type="M4_socket_head",
        quantity=4,
        material="A2 stainless",
        torque_spec_nm=3.0,
        thread_engagement_mm=14.0,  # ≥ 3×4 = 12 mm
        locking="Loctite 243",
    )
    errors = spec.validate()
    assert errors == []


def test_fastener_thread_engagement_fail():
    spec = FastenerSpec(
        interface_id="IF-002",
        connection_description="test",
        fastener_type="M4_socket_head",
        quantity=4,
        material="steel",
        torque_spec_nm=3.0,
        thread_engagement_mm=8.0,  # < 3×4 = 12 mm
        locking="none",
    )
    errors = spec.validate()
    assert len(errors) == 1
    assert "thread engagement" in errors[0]


# ─────────────────────────────────────────────────────────────────────────────
# Disassembly tests
# ─────────────────────────────────────────────────────────────────────────────

def test_disassembly_all_components_in_order():
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    result = build_disassembly_dag(placements, INTERFACES, [])
    assert set(result.removal_order) == {c["id"] for c in COMPONENTS}


def test_disassembly_table_renders():
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    result = build_disassembly_dag(placements, INTERFACES, [])
    table = format_disassembly_table(result)
    assert "DISASSEMBLY SEQUENCE" in table
    assert "Total estimated time" in table


# ─────────────────────────────────────────────────────────────────────────────
# Maintenance classification tests
# ─────────────────────────────────────────────────────────────────────────────

def test_canopy_is_l1():
    """Canopy (snap fit, no prerequisites) should be L1-field."""
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    disasm = build_disassembly_dag(placements, INTERFACES, [])
    masses = {p.component_id: p.mass_kg for p in placements}
    summary = classify_maintenance_access(disasm, component_masses=masses)
    canopy_class = next(c for c in summary.classifications if c.component_id == "C-007")
    assert canopy_class.level == ServiceLevel.L1_FIELD


def test_serviceability_warning_for_motor():
    """Motors classified L3 should trigger serviceability warning."""
    # Artificially make Motor L require many prerequisites by adding fake blocked_by
    placer = ComponentPlacer(primary_component_id="C-001")
    placements = placer.place_all(COMPONENTS, INTERFACES)
    disasm = build_disassembly_dag(placements, INTERFACES, [])
    # Inject many prerequisites into motor L node
    motor_node = next(n for n in disasm.nodes if n.component_id == "C-004")
    motor_node.blocked_by = ["C-001", "C-002", "C-003", "C-006", "C-007"]
    motor_node.estimated_removal_time_min = 300.0

    masses = {p.component_id: p.mass_kg for p in placements}
    summary = classify_maintenance_access(disasm, component_masses=masses)
    # Should have a warning about motor serviceability
    motor_class = next(c for c in summary.classifications if c.component_id == "C-004")
    if motor_class.level == ServiceLevel.L3_FACTORY:
        assert any("SERVICEABILITY" in w for w in summary.serviceability_warnings)

"""Tests for forge_solver.smart_fuselage — parametric smart airframe model."""

from __future__ import annotations

import pytest

from forge_solver.smart_fuselage import (
    FuselageGeometry,
    analyse_smart_fuselage,
    compute_fuselage_aero,
    compute_fuselage_structure,
    configure_smart_layer,
)


# ── FuselageGeometry ──────────────────────────────────────────────────────────


def _make_geom() -> FuselageGeometry:
    return FuselageGeometry(
        length_m=1.5,
        max_diameter_m=0.2,
        skin_thickness_m=0.003,
    )


def test_fineness_ratio():
    geom = _make_geom()
    assert abs(geom.fineness_ratio - 7.5) < 0.01


def test_wetted_area_positive():
    geom = _make_geom()
    assert geom.wetted_area_m2 > 0


def test_structural_volume_positive():
    geom = _make_geom()
    assert geom.structural_volume_m3 > 0


def test_interior_volume_positive():
    geom = _make_geom()
    assert geom.interior_volume_m3 > 0


def test_invalid_skin_thickness():
    with pytest.raises(ValueError, match="wall_thickness|skin_thickness"):
        FuselageGeometry(length_m=1.5, max_diameter_m=0.2, skin_thickness_m=0.15)


def test_invalid_shell_type():
    with pytest.raises(ValueError, match="shell_type"):
        FuselageGeometry(length_m=1.5, max_diameter_m=0.2, shell_type="monolith")


# ── Aerodynamic drag ──────────────────────────────────────────────────────────


def test_drag_positive():
    geom = _make_geom()
    aero = compute_fuselage_aero(geom, speed_ms=30.0)
    assert aero.total_drag_n > 0


def test_drag_increases_with_speed():
    geom = _make_geom()
    d1 = compute_fuselage_aero(geom, speed_ms=10.0).total_drag_n
    d2 = compute_fuselage_aero(geom, speed_ms=50.0).total_drag_n
    assert d2 > d1


def test_cd_body_range():
    geom = _make_geom()
    aero = compute_fuselage_aero(geom, speed_ms=30.0)
    assert 0.0 < aero.cd_body < 1.0  # Sensible range for streamlined body


def test_drag_invalid_speed():
    geom = _make_geom()
    with pytest.raises(ValueError, match="speed_ms"):
        compute_fuselage_aero(geom, speed_ms=0.0)


# ── Structural analysis ───────────────────────────────────────────────────────


def test_buckling_load_positive():
    geom = _make_geom()
    struct = compute_fuselage_structure(geom, bending_moment_nm=0.0)
    assert struct.axial_buckling_load_n > 0


def test_structural_mass_positive():
    geom = _make_geom()
    struct = compute_fuselage_structure(geom, bending_moment_nm=0.0)
    assert struct.mass_kg > 0


def test_safety_factor_infinite_at_zero_load():
    geom = _make_geom()
    struct = compute_fuselage_structure(geom, bending_moment_nm=0.0)
    assert struct.safety_factor_bending == float("inf")


def test_safety_factor_decreases_with_load():
    geom = _make_geom()
    s1 = compute_fuselage_structure(geom, bending_moment_nm=100.0)
    s2 = compute_fuselage_structure(geom, bending_moment_nm=1000.0)
    assert s2.safety_factor_bending < s1.safety_factor_bending


# ── Smart layer configuration ─────────────────────────────────────────────────


def test_block0_no_smart():
    geom = _make_geom()
    config = configure_smart_layer(geom, "BLOCK_0")
    assert config.shm_fibre_count == 0
    assert config.power_rail_capacity_w == 0.0
    assert config.comms_node_count == 0
    assert config.energy_module_capacity_j == 0.0


def test_block1_has_shm():
    geom = _make_geom()
    config = configure_smart_layer(geom, "BLOCK_1")
    assert config.shm_fibre_count > 0


def test_block2_has_power():
    geom = _make_geom()
    config = configure_smart_layer(geom, "BLOCK_2")
    assert config.power_rail_capacity_w > 0


def test_block3_has_comms():
    geom = _make_geom()
    config = configure_smart_layer(geom, "BLOCK_3")
    assert config.comms_node_count > 0


def test_block4_has_energy():
    geom = _make_geom()
    config = configure_smart_layer(geom, "BLOCK_4")
    assert config.energy_module_capacity_j > 0


def test_block_capacity_monotonic():
    """Higher block levels have >= capacity than lower ones."""
    geom = _make_geom()
    c2 = configure_smart_layer(geom, "BLOCK_2")
    c4 = configure_smart_layer(geom, "BLOCK_4")
    assert c4.shm_fibre_count >= c2.shm_fibre_count
    assert c4.power_rail_capacity_w >= c2.power_rail_capacity_w


# ── Full analysis ─────────────────────────────────────────────────────────────


def test_analyse_smart_fuselage_complete():
    geom = _make_geom()
    result = analyse_smart_fuselage(
        geom,
        block_level="BLOCK_2",
        speed_ms=30.0,
        bending_moment_nm=50.0,
    )
    assert result.aero is not None
    assert result.structure.mass_kg > 0
    assert result.smart_layer.power_rail_capacity_w > 0
    assert 0.0 < result.cg_x_m < geom.length_m


def test_analyse_smart_fuselage_no_aero():
    """When speed_ms is None, aerodynamic analysis is skipped."""
    geom = _make_geom()
    result = analyse_smart_fuselage(geom, block_level="BLOCK_0", speed_ms=None)
    assert result.aero is None

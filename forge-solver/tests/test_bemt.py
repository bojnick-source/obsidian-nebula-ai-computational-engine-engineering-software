"""Tests for forge_solver.bemt — Blade Element Momentum Theory solver."""

from __future__ import annotations

import pytest

from forge_solver.bemt import (
    BEMTCondition,
    BladeElement,
    RotorGeometry,
    compute_rotor_efficiency,
    discretize_rotor,
    hover_thrust,
)


# ── Data class validation ─────────────────────────────────────────────────────


def test_blade_element_invalid_radius():
    with pytest.raises(ValueError, match="radius_m"):
        BladeElement(radius_m=-0.1, chord_m=0.05, twist_rad=0.2, cl_alpha=5.73, cd0=0.01)


def test_rotor_geometry_invalid_blades():
    with pytest.raises(ValueError, match="n_blades"):
        RotorGeometry(n_blades=0, tip_radius_m=0.3, hub_radius_m=0.03,
                      root_chord_m=0.05, tip_chord_m=0.03,
                      root_twist_rad=0.3, tip_twist_rad=0.05)


def test_rotor_geometry_hub_exceeds_tip():
    with pytest.raises(ValueError, match="hub_radius_m"):
        RotorGeometry(n_blades=2, tip_radius_m=0.3, hub_radius_m=0.5,
                      root_chord_m=0.05, tip_chord_m=0.03,
                      root_twist_rad=0.3, tip_twist_rad=0.05)


# ── Discretise rotor ──────────────────────────────────────────────────────────


def _make_geom():
    return RotorGeometry(
        n_blades=2,
        tip_radius_m=0.3,
        hub_radius_m=0.03,
        root_chord_m=0.05,
        tip_chord_m=0.025,
        root_twist_rad=0.4,
        tip_twist_rad=0.05,
    )


def test_discretize_rotor_count():
    geom = _make_geom()
    elements = discretize_rotor(geom, cl_alpha=5.73, cd0=0.01, n_stations=20)
    assert len(elements) == 20


def test_discretize_rotor_radii_ordered():
    geom = _make_geom()
    elements = discretize_rotor(geom, cl_alpha=5.73, cd0=0.01, n_stations=20)
    radii = [e.radius_m for e in elements]
    assert radii == sorted(radii)


def test_discretize_rotor_min_stations():
    geom = _make_geom()
    elements = discretize_rotor(geom, cl_alpha=5.73, cd0=0.01, n_stations=2)
    assert len(elements) >= 10  # clamped to _MIN_STATIONS


# ── BEMT solve ────────────────────────────────────────────────────────────────


def test_hover_thrust_positive():
    geom = _make_geom()
    thrust = hover_thrust(geom, rpm=3000.0)
    assert thrust > 0.0


def test_hover_thrust_increases_with_rpm():
    geom = _make_geom()
    t1 = hover_thrust(geom, rpm=2000.0)
    t2 = hover_thrust(geom, rpm=4000.0)
    assert t2 > t1


def test_compute_rotor_efficiency_keys():
    geom = _make_geom()
    result = compute_rotor_efficiency(geom, rpm=3000.0)
    assert "thrust_n" in result
    assert "power_w" in result
    assert "figure_of_merit" in result
    assert "disk_loading_pa" in result


def test_figure_of_merit_range():
    geom = _make_geom()
    result = compute_rotor_efficiency(geom, rpm=3000.0)
    # FM should be between 0 and 1 for a physical rotor
    assert 0.0 <= result["figure_of_merit"] <= 1.0


def test_disk_loading_positive():
    geom = _make_geom()
    result = compute_rotor_efficiency(geom, rpm=3000.0)
    assert result["disk_loading_pa"] > 0.0


def test_bemt_condition_invalid_rpm():
    with pytest.raises(ValueError, match="rpm"):
        BEMTCondition(rpm=0.0, climb_speed_ms=0.0, air_density_kg_m3=1.225)

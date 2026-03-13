"""Tests for forge_solver.fea — Euler-Bernoulli beam FEA solver."""

from __future__ import annotations


import pytest

from forge_solver.fea import (
    BeamDesign,
    evaluate_design_fea,
    generate_beam_mesh,
    solve_static,
)


# ── BeamDesign validation ─────────────────────────────────────────────────────


def test_beam_design_invalid_wall():
    with pytest.raises(ValueError, match="wall_thickness"):
        BeamDesign(
            length_m=1.0,
            outer_diameter_m=0.05,
            wall_thickness_m=0.03,  # > D/2
            elastic_modulus_pa=70e9,
            yield_strength_pa=500e6,
        )


# ── Mesh generation ───────────────────────────────────────────────────────────


def test_mesh_node_count():
    design = BeamDesign(
        length_m=1.0,
        outer_diameter_m=0.05,
        wall_thickness_m=0.003,
        elastic_modulus_pa=70e9,
        yield_strength_pa=500e6,
        n_elements=10,
    )
    nodes, elements = generate_beam_mesh(design)
    assert len(nodes) == 11
    assert len(elements) == 10


# ── FEA solve ─────────────────────────────────────────────────────────────────


def _make_design(n_elements: int = 10) -> BeamDesign:
    return BeamDesign(
        length_m=0.5,
        outer_diameter_m=0.03,
        wall_thickness_m=0.002,
        elastic_modulus_pa=70e9,
        yield_strength_pa=400e6,
        n_elements=n_elements,
    )


def test_solve_static_converged():
    design = _make_design()
    result = solve_static(design, tip_load_n=10.0)
    assert result.converged


def test_solve_static_tip_displacement_positive():
    """Tip deflects in the load direction."""
    design = _make_design()
    result = solve_static(design, tip_load_n=10.0)
    assert result.max_displacement_m > 0.0


def test_solve_static_zero_load():
    """Zero load → zero displacement."""
    design = _make_design()
    result = solve_static(design, tip_load_n=0.0)
    assert result.max_displacement_m < 1e-12


def test_deflection_increases_with_load():
    design = _make_design()
    r1 = solve_static(design, tip_load_n=5.0)
    r2 = solve_static(design, tip_load_n=50.0)
    assert r2.max_displacement_m > r1.max_displacement_m


def test_deflection_linear_in_load():
    """Euler-Bernoulli beam is linear: doubling load doubles deflection."""
    design = _make_design(n_elements=20)
    r1 = solve_static(design, tip_load_n=10.0)
    r2 = solve_static(design, tip_load_n=20.0)
    ratio = r2.max_displacement_m / r1.max_displacement_m
    assert abs(ratio - 2.0) < 0.05  # within 5%


def test_element_stresses_populated():
    design = _make_design()
    result = solve_static(design, tip_load_n=10.0)
    assert len(result.element_stresses) == design.n_elements


def test_safety_factor_positive():
    design = _make_design()
    result = solve_static(design, tip_load_n=10.0)
    for stress in result.element_stresses:
        assert stress.safety_factor > 0.0


def test_evaluate_design_fea_convenience():
    result = evaluate_design_fea(
        length_m=0.5,
        outer_diameter_m=0.03,
        wall_thickness_m=0.002,
        tip_load_n=10.0,
    )
    assert result.converged
    assert result.max_displacement_m > 0

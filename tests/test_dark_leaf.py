"""Smoke + regression tests for dark-leaf-v2 physics solvers and digital-thread stack.

Covers:
- reidce: aerospace, bemt, energy_maneuverability, fea, ratio, wind_tunnel
- sfcs_mdp: cypher_forge (integrity + cipher loop + BEMT surrogate + session signing)
"""
from __future__ import annotations

import math

import pytest

# ---------------------------------------------------------------------------
# reidce.aerospace
# ---------------------------------------------------------------------------


def test_isa_atmosphere_sea_level():
    from reidce.aerospace import isa_atmosphere

    atm = isa_atmosphere(0.0)
    assert abs(atm.temperature_k - 288.15) < 0.01
    assert abs(atm.pressure_pa - 101325.0) < 1.0
    assert abs(atm.density_kg_m3 - 1.225) < 0.01


def test_isa_atmosphere_11000m():
    from reidce.aerospace import isa_atmosphere

    atm = isa_atmosphere(11000.0)
    assert atm.temperature_k < 288.15
    assert atm.pressure_pa < 101325.0


def test_lift_drag_values():
    from reidce.aerospace import AeroCoefficients, isa_atmosphere, lift_drag

    atm = isa_atmosphere(0.0)
    coeffs = AeroCoefficients(cl=1.0, cd=0.05)
    result = lift_drag(50.0, 10.0, coeffs, atm.density_kg_m3)
    assert result["lift_n"] > 0
    assert result["drag_n"] > 0
    assert abs(result["lift_n"] / result["drag_n"] - 20.0) < 0.01


def test_glide_ratio():
    from reidce.aerospace import AeroCoefficients, estimate_glide_ratio

    coeffs = AeroCoefficients(cl=1.0, cd=0.05)
    assert abs(estimate_glide_ratio(coeffs) - 20.0) < 1e-9


def test_range_endurance_positive():
    from reidce.aerospace import range_endurance

    result = range_endurance(50.0, 1_000_000.0, 5.0, efficiency=0.35)
    assert result.range_km > 0
    assert result.endurance_s > 0


def test_lift_drag_bad_inputs():
    from reidce.aerospace import AeroCoefficients, lift_drag

    with pytest.raises(ValueError):
        lift_drag(0.0, 10.0, AeroCoefficients(cl=1.0, cd=0.05), 1.225)


# ---------------------------------------------------------------------------
# reidce.bemt
# ---------------------------------------------------------------------------


def test_bemt_hover_thrust_positive():
    from reidce.bemt import BEMTCondition, RotorGeometry, hover_thrust

    geom = RotorGeometry(radius_m=0.127, n_blades=2)
    cond = BEMTCondition(rpm=5000.0, rho_kg_m3=1.225)
    thrust = hover_thrust(geom, cond)
    assert thrust > 0.0


def test_bemt_solve_returns_result():
    from reidce.bemt import BEMTCondition, RotorGeometry, solve_bemt

    geom = RotorGeometry(radius_m=0.127, n_blades=2)
    cond = BEMTCondition(rpm=5000.0, rho_kg_m3=1.225)
    result = solve_bemt(geom, cond)
    assert result.thrust_n >= 0.0
    assert result.power_w >= 0.0
    assert 0.0 <= result.fm <= 1.1


def test_compute_rotor_efficiency():
    from reidce.bemt import BEMTCondition, RotorGeometry, compute_rotor_efficiency

    geom = RotorGeometry(radius_m=0.127, n_blades=2)
    cond = BEMTCondition(rpm=5000.0, rho_kg_m3=1.225)
    metrics = compute_rotor_efficiency(geom, cond)
    assert metrics["thrust"] >= 0.0
    assert metrics["power"] >= 0.0
    assert metrics["efficiency"] >= 0.0


# ---------------------------------------------------------------------------
# reidce.energy_maneuverability
# ---------------------------------------------------------------------------


def test_specific_energy():
    from reidce.energy_maneuverability import specific_energy

    he = specific_energy(100.0, 1000.0)
    assert abs(he - (100.0**2 / (2 * 9.80665) + 1000.0)) < 0.01


def test_specific_excess_power():
    from reidce.energy_maneuverability import specific_excess_power

    ps = specific_excess_power(
        thrust_n=200.0, drag_n=50.0, weight_n=980.665, speed_m_s=30.0
    )
    assert isinstance(ps, float)


def test_em_envelope_returns_list():
    from reidce.energy_maneuverability import (
        Atmosphere,
        StructuralLimits,
        VehicleParams,
        compute_em_envelope,
    )

    params = VehicleParams(mass_kg=1.5, max_thrust_n=30.0, wing_area_m2=0.06, cd0=0.03)
    atm = Atmosphere()
    limits = StructuralLimits(max_g=3.0, max_speed_m_s=60.0)
    envelope = compute_em_envelope(params, atm, limits, speeds_m_s=[20.0, 40.0], altitudes_m=[0.0])
    assert len(envelope) > 0


# ---------------------------------------------------------------------------
# reidce.fea
# ---------------------------------------------------------------------------


def test_cantilever_fea_converges():
    from reidce.fea import cantilever_fea

    result = cantilever_fea(
        diameter_m=0.01,
        wall_thickness_m=0.001,
        length_m=0.2,
        tip_load_n=10.0,
    )
    assert result.converged
    assert result.max_displacement_m > 0.0
    assert result.max_von_mises_pa > 0.0


def test_fea_safety_factor_positive():
    from reidce.fea import cantilever_fea

    result = cantilever_fea(tip_load_n=1.0, yield_stress_pa=250e6)
    for es in result.element_stresses:
        assert es.safety_factor > 0.0


def test_generate_beam_mesh_node_count():
    from reidce.fea import generate_beam_mesh

    mesh = generate_beam_mesh(diameter_m=0.01, wall_thickness_m=0.001, length_m=0.2, n_elements=8)
    assert mesh.node_count == 9
    assert mesh.element_count == 8


# ---------------------------------------------------------------------------
# reidce.ratio
# ---------------------------------------------------------------------------


def test_parse_ratio_canonical():
    from reidce.ratio import parse_ratio

    r = parse_ratio("4:1")
    assert r.numerator == 4
    assert r.denominator == 1


def test_parse_ratio_reduces():
    from reidce.ratio import parse_ratio

    r = parse_ratio("8:2")
    assert r.numerator == 4
    assert r.denominator == 1


def test_parse_ratio_slash():
    from reidce.ratio import parse_ratio

    r = parse_ratio("3/1")
    assert r.numerator == 3


def test_parse_ratio_zero_denominator():
    from reidce.ratio import parse_ratio

    with pytest.raises((ValueError, ZeroDivisionError)):
        parse_ratio("4:0")


# ---------------------------------------------------------------------------
# reidce.wind_tunnel
# ---------------------------------------------------------------------------


def test_compute_aero_returns_result():
    from reidce.wind_tunnel import AirfoilGeometry, FlowCondition, compute_aero

    geom = AirfoilGeometry(chord_m=0.3, span_m=5.0, thickness_ratio=0.12, camber_ratio=0.02)
    cond = FlowCondition(velocity_m_s=50.0, alpha_rad=math.radians(5.0))
    result = compute_aero(geom, cond)
    assert result.cl > 0.0
    assert result.cd > 0.0


def test_run_wind_tunnel_sweep():
    from reidce.wind_tunnel import AirfoilGeometry, run_wind_tunnel

    geom = AirfoilGeometry(chord_m=0.3, span_m=5.0, thickness_ratio=0.12, camber_ratio=0.02)
    wt = run_wind_tunnel(geom, velocities_m_s=[50.0], alphas_deg=[-4.0, 0.0, 4.0, 8.0])
    assert len(wt.sweep) >= 4


def test_dryden_gust_length():
    from reidce.wind_tunnel import DrydenGust, dryden_gust_velocities

    gust = DrydenGust(intensity_m_s=1.5, length_scale_m=30.0, seed=42)
    time_s = [i * 0.02 for i in range(50)]
    gusts = dryden_gust_velocities(gust, time_s, airspeed_m_s=20.0)
    assert len(gusts) == 50


# ---------------------------------------------------------------------------
# sfcs_mdp.cypher_forge — integrity (HMAC)
# ---------------------------------------------------------------------------


def test_compute_verify_hmac_roundtrip():
    from sfcs_mdp.cypher_forge import compute_hmac, verify_hmac

    data = b"build-artifact-payload"
    tag = compute_hmac(data, "BUILD-001", "REV-A")
    assert verify_hmac(data, tag, "BUILD-001", "REV-A")


def test_hmac_wrong_build_id_fails():
    from sfcs_mdp.cypher_forge import compute_hmac, verify_hmac

    data = b"payload"
    tag = compute_hmac(data, "BUILD-001", "REV-A")
    assert not verify_hmac(data, tag, "BUILD-002", "REV-A")


def test_cipher_metadata_fields():
    from sfcs_mdp.cypher_forge import cipher_metadata

    meta = cipher_metadata("B-1", "R-1")
    assert meta["build_id"] == "B-1"
    assert meta["rev_tag"] == "R-1"
    assert "cipher_algorithm" in meta


# ---------------------------------------------------------------------------
# sfcs_mdp.cypher_forge — sign_session_result
# ---------------------------------------------------------------------------


def test_sign_session_result_has_hmac():
    import json

    from sfcs_mdp.cypher_forge import sign_session_result
    from sfcs_mdp.cypher_forge import verify_hmac

    summary = {"programme": "TEST", "version": "1", "iterations": 3, "final_status": "converged"}
    signed = sign_session_result(summary, "BUILD-X", "REV-Y")

    assert "cipher" in signed
    assert "hmac_hex" in signed["cipher"]

    payload_bytes = json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert verify_hmac(payload_bytes, signed["cipher"]["hmac_hex"], "BUILD-X", "REV-Y")


# ---------------------------------------------------------------------------
# sfcs_mdp.cypher_forge — make_bemt_predict_fn + CypherForgeSession
# ---------------------------------------------------------------------------


def test_make_bemt_predict_fn_returns_metrics():
    from sfcs_mdp.cypher_forge import make_bemt_predict_fn

    predict = make_bemt_predict_fn()
    result = predict([5000.0])
    assert "thrust_n" in result
    assert "power_w" in result
    assert result["thrust_n"] >= 0.0


def test_cypher_forge_session_bemt_converges_or_runs():
    from sfcs_mdp.cypher_forge import CypherForgeSession, make_bemt_predict_fn

    predict = make_bemt_predict_fn()
    session = CypherForgeSession(
        predict_fn=predict,
        constraints={"thrust_n": (0.0, 100.0)},
        max_iterations=3,
        noise_scale=0.01,
        seed=0,
    )
    history = session.run([5000.0])
    assert len(history) >= 1
    assert history[-1].status in ("continue", "converged", "unsafe")


def test_cypher_forge_session_summary_keys():
    from sfcs_mdp.cypher_forge import CypherForgeSession

    session = CypherForgeSession(
        predict_fn=lambda inputs: {"x": inputs[0]},
        max_iterations=2,
    )
    session.run([1.0])
    s = session.summary()
    assert s["programme"] == "DARPA_CyPhER_Forge"
    assert s["iterations"] >= 1


# ---------------------------------------------------------------------------
# sfcs_mdp.v2_engine
# ---------------------------------------------------------------------------


def test_find_engine_cli_missing_hint_returns_none():
    from sfcs_mdp.v2_engine import find_engine_cli

    result = find_engine_cli(hint="/nonexistent/path/v2_engine_cli")
    assert result is None


def test_run_engine_missing_binary_raises():
    from sfcs_mdp.v2_engine import run_engine

    with pytest.raises(RuntimeError):
        run_engine("/nonexistent/v2_engine_cli", "{}")

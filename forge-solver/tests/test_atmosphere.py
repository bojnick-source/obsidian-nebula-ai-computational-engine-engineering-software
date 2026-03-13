"""Tests for forge_solver.atmosphere — ISA model and aerodynamic utilities."""

from __future__ import annotations


import pytest

from forge_solver.atmosphere import (
    AeroCoefficients,
    isa_atmosphere,
    lift_drag,
    range_endurance,
    thrust_to_weight,
    wing_loading,
)


# ── ISA model ─────────────────────────────────────────────────────────────────


def test_isa_sea_level_density():
    atm = isa_atmosphere(0.0)
    assert abs(atm.density_kg_m3 - 1.225) < 0.005


def test_isa_sea_level_temperature():
    atm = isa_atmosphere(0.0)
    assert abs(atm.temperature_k - 288.15) < 0.01


def test_isa_sea_level_pressure():
    atm = isa_atmosphere(0.0)
    assert abs(atm.pressure_pa - 101_325.0) < 1.0


def test_isa_altitude_density_decreases():
    atm0 = isa_atmosphere(0.0)
    atm5k = isa_atmosphere(5000.0)
    atm11k = isa_atmosphere(11_000.0)
    assert atm5k.density_kg_m3 < atm0.density_kg_m3
    assert atm11k.density_kg_m3 < atm5k.density_kg_m3


def test_isa_stratosphere_isothermal():
    """Above tropopause, temperature should be constant at 216.65 K."""
    atm_strat1 = isa_atmosphere(12_000.0)
    atm_strat2 = isa_atmosphere(20_000.0)
    assert abs(atm_strat1.temperature_k - 216.65) < 0.1
    assert abs(atm_strat2.temperature_k - 216.65) < 0.1


def test_isa_speed_of_sound_sea_level():
    atm = isa_atmosphere(0.0)
    # ~340 m/s at sea level
    assert 335.0 < atm.speed_of_sound_ms < 345.0


# ── Aerodynamic forces ────────────────────────────────────────────────────────


def test_lift_drag_positive():
    atm = isa_atmosphere(0.0)
    coeffs = AeroCoefficients(cl=1.0, cd=0.05)
    lift, drag = lift_drag(atm, speed_ms=50.0, wing_area_m2=1.0, coeffs=coeffs)
    assert lift > 0
    assert drag > 0
    assert lift > drag  # L/D = 20


def test_lift_drag_invalid_area():
    atm = isa_atmosphere(0.0)
    coeffs = AeroCoefficients(cl=1.0, cd=0.05)
    with pytest.raises(ValueError, match="wing_area_m2"):
        lift_drag(atm, speed_ms=50.0, wing_area_m2=-1.0, coeffs=coeffs)


def test_lift_drag_invalid_speed():
    atm = isa_atmosphere(0.0)
    coeffs = AeroCoefficients(cl=1.0, cd=0.05)
    with pytest.raises(ValueError, match="speed_ms"):
        lift_drag(atm, speed_ms=0.0, wing_area_m2=1.0, coeffs=coeffs)


def test_aero_coefficients_negative_cd():
    with pytest.raises(ValueError, match="cd"):
        AeroCoefficients(cl=1.0, cd=-0.01)


# ── Range/endurance ───────────────────────────────────────────────────────────


def test_range_endurance_positive():
    result = range_endurance(
        mass_kg=5.0,
        usable_energy_j_per_kg=1_000_000.0,  # 1 MJ/kg
        power_w=100.0,
        cruise_speed_ms=15.0,
    )
    assert result.range_m > 0
    assert result.endurance_s > 0


def test_range_endurance_invalid_efficiency():
    with pytest.raises(ValueError, match="efficiency"):
        range_endurance(
            mass_kg=5.0,
            usable_energy_j_per_kg=1e6,
            power_w=100.0,
            cruise_speed_ms=15.0,
            efficiency=1.5,
        )


def test_wing_loading_basic():
    wl = wing_loading(weight_n=500.0, wing_area_m2=2.5)
    assert abs(wl - 200.0) < 0.1


def test_thrust_to_weight():
    assert abs(thrust_to_weight(thrust_n=100.0, weight_n=50.0) - 2.0) < 1e-9

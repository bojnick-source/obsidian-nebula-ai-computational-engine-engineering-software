"""International Standard Atmosphere (ISA) model and aerodynamic force utilities.

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/reidce/aerospace.py)

C++ accuracy layer:
  For accuracy-critical inner loops (e.g., trajectory optimisation with thousands of
  ISA evaluations), use forge-core's fuselage_aero.hpp which shares the same constants.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ── ISA constants (SI) ────────────────────────────────────────────────────────
_T0_K: float = 288.15       # Sea-level temperature [K]
_P0_PA: float = 101_325.0   # Sea-level pressure [Pa]
_RHO0_KGM3: float = 1.225   # Sea-level density [kg/m³]
_LAPSE_K_PER_M: float = 0.0065  # Tropospheric lapse rate [K/m]
_G0_MS2: float = 9.80665    # Standard gravity [m/s²]
_R_J_KGMOL: float = 287.058  # Specific gas constant for dry air [J/(kg·K)]
_TROPOPAUSE_M: float = 11_000.0  # Troposphere ceiling [m]
_T_STRAT_K: float = 216.65  # Isothermal stratosphere temperature [K]

# ── Aerodynamic model limits ──────────────────────────────────────────────────
_MIN_WING_AREA_M2: float = 1e-6
_MIN_EFFICIENCY: float = 0.01
_MAX_EFFICIENCY: float = 1.0


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ISAAtmosphere:
    """Atmospheric state at a given altitude."""

    altitude_m: float
    temperature_k: float
    pressure_pa: float
    density_kg_m3: float

    @property
    def speed_of_sound_ms(self) -> float:
        """Speed of sound [m/s] (perfect gas, gamma=1.4)."""
        return math.sqrt(1.4 * _R_J_KGMOL * self.temperature_k)


@dataclass(frozen=True)
class AeroCoefficients:
    """Non-dimensional aerodynamic coefficients."""

    cl: float  # Lift coefficient
    cd: float  # Drag coefficient

    def __post_init__(self) -> None:
        if self.cd < 0:
            raise ValueError(f"cd must be >= 0, got {self.cd}")


@dataclass(frozen=True)
class RangeEstimate:
    """Cruise range and endurance estimates."""

    range_m: float       # Estimated range [m]
    endurance_s: float   # Estimated endurance [s]
    cruise_speed_ms: float  # Optimal cruise speed [m/s]


# ── ISA model ─────────────────────────────────────────────────────────────────


def isa_atmosphere(altitude_m: float) -> ISAAtmosphere:
    """Return ISA atmospheric state at *altitude_m* above MSL.

    Handles two standard layers:
      - Troposphere  (0 – 11 000 m): constant lapse rate
      - Low stratosphere (> 11 000 m): isothermal at 216.65 K

    Args:
        altitude_m: Geometric altitude in metres (may be negative for underground
                    test cases, but pressures below MSL follow the troposphere model).

    Returns:
        :class:`ISAAtmosphere` with temperature, pressure, and density.
    """
    if altitude_m <= _TROPOPAUSE_M:
        temperature_k = _T0_K - _LAPSE_K_PER_M * altitude_m
        pressure_pa = _P0_PA * (temperature_k / _T0_K) ** (_G0_MS2 / (_LAPSE_K_PER_M * _R_J_KGMOL))
    else:
        # Isothermal stratosphere
        temperature_k = _T_STRAT_K
        # Pressure at tropopause boundary
        t_trop = _T0_K - _LAPSE_K_PER_M * _TROPOPAUSE_M
        p_trop = _P0_PA * (t_trop / _T0_K) ** (_G0_MS2 / (_LAPSE_K_PER_M * _R_J_KGMOL))
        # Exponential decay above tropopause
        pressure_pa = p_trop * math.exp(
            -_G0_MS2 * (altitude_m - _TROPOPAUSE_M) / (_R_J_KGMOL * _T_STRAT_K)
        )

    density_kg_m3 = pressure_pa / (_R_J_KGMOL * temperature_k)
    return ISAAtmosphere(
        altitude_m=altitude_m,
        temperature_k=temperature_k,
        pressure_pa=pressure_pa,
        density_kg_m3=density_kg_m3,
    )


# ── Aerodynamic forces ────────────────────────────────────────────────────────


def lift_drag(
    atm: ISAAtmosphere,
    speed_ms: float,
    wing_area_m2: float,
    coeffs: AeroCoefficients,
) -> tuple[float, float]:
    """Compute lift and drag forces [N].

    Uses the standard aerodynamic force expression:
      F = 0.5 · ρ · V² · S · C

    Args:
        atm:          Atmospheric state from :func:`isa_atmosphere`.
        speed_ms:     True airspeed [m/s].
        wing_area_m2: Reference wing area [m²].
        coeffs:       Lift and drag coefficients.

    Returns:
        ``(lift_N, drag_N)`` tuple.

    Raises:
        ValueError: On non-positive wing area or speed.
    """
    if wing_area_m2 <= 0:
        raise ValueError(f"wing_area_m2 must be positive, got {wing_area_m2}")
    if speed_ms <= 0:
        raise ValueError(f"speed_ms must be positive, got {speed_ms}")

    q = 0.5 * atm.density_kg_m3 * speed_ms ** 2  # dynamic pressure [Pa]
    lift_n = q * wing_area_m2 * coeffs.cl
    drag_n = q * wing_area_m2 * coeffs.cd
    return lift_n, drag_n


def estimate_glide_ratio(coeffs: AeroCoefficients) -> float:
    """Return L/D ratio.

    Raises:
        ValueError: If drag coefficient is zero.
    """
    if coeffs.cd == 0:
        raise ValueError("Drag coefficient is zero — glide ratio undefined")
    return coeffs.cl / coeffs.cd


def wing_loading(weight_n: float, wing_area_m2: float) -> float:
    """Return wing loading W/S [Pa = N/m²].

    Raises:
        ValueError: On non-positive inputs.
    """
    if weight_n <= 0:
        raise ValueError(f"weight_n must be positive, got {weight_n}")
    if wing_area_m2 < _MIN_WING_AREA_M2:
        raise ValueError(f"wing_area_m2 must be > {_MIN_WING_AREA_M2}, got {wing_area_m2}")
    return weight_n / wing_area_m2


def thrust_to_weight(thrust_n: float, weight_n: float) -> float:
    """Return thrust-to-weight ratio (dimensionless).

    Raises:
        ValueError: On non-positive weight.
    """
    if weight_n <= 0:
        raise ValueError(f"weight_n must be positive, got {weight_n}")
    return thrust_n / weight_n


def range_endurance(
    mass_kg: float,
    usable_energy_j_per_kg: float,
    power_w: float,
    cruise_speed_ms: float,
    efficiency: float = 0.85,
) -> RangeEstimate:
    """Estimate cruise range and endurance from energy and power.

    Args:
        mass_kg:               Aircraft total mass [kg].
        usable_energy_j_per_kg: Specific energy of the energy source [J/kg].
        power_w:               Cruise power consumption [W].
        cruise_speed_ms:       Cruise true airspeed [m/s].
        efficiency:            Propulsive efficiency (0.01–1.0).

    Returns:
        :class:`RangeEstimate` with range, endurance, and cruise speed.

    Raises:
        ValueError: On invalid inputs.
    """
    if mass_kg <= 0:
        raise ValueError(f"mass_kg must be positive, got {mass_kg}")
    if usable_energy_j_per_kg <= 0:
        raise ValueError(f"usable_energy_j_per_kg must be positive, got {usable_energy_j_per_kg}")
    if power_w <= 0:
        raise ValueError(f"power_w must be positive, got {power_w}")
    if cruise_speed_ms <= 0:
        raise ValueError(f"cruise_speed_ms must be positive, got {cruise_speed_ms}")
    if not (_MIN_EFFICIENCY <= efficiency <= _MAX_EFFICIENCY):
        raise ValueError(f"efficiency must be in [{_MIN_EFFICIENCY}, {_MAX_EFFICIENCY}], got {efficiency}")

    total_energy_j = usable_energy_j_per_kg * mass_kg * efficiency
    endurance_s = total_energy_j / power_w
    range_m = endurance_s * cruise_speed_ms
    return RangeEstimate(
        range_m=range_m,
        endurance_s=endurance_s,
        cruise_speed_ms=cruise_speed_ms,
    )

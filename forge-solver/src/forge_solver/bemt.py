"""Blade Element Momentum Theory (BEMT) rotor solver.

Iterates to match momentum-theory and blade-element-theory inflow predictions at
each radial station using under-relaxation for stable convergence.

C++ accuracy layer:
  The inner inflow iteration (bemt_core.hpp / bemt_core.cpp in forge-core/) implements
  the same algorithm in float64 C++20 for deterministic, timing-critical usage.

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/reidce/bemt.py)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ── Solver constants ──────────────────────────────────────────────────────────
_BEMT_MAX_ITER: int = 200
_BEMT_TOLERANCE: float = 1e-6   # Inflow ratio convergence threshold
_BEMT_RELAX: float = 0.5        # Under-relaxation factor (0 < α < 1)
_HUB_RADIUS_FRACTION: float = 0.1  # Default hub/tip ratio when not specified
_MIN_STATIONS: int = 10         # Minimum radial discretisation stations
_MAX_STATIONS: int = 500


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BladeElement:
    """Aerodynamic and geometric properties of one radial blade station."""

    radius_m: float         # Radial position [m]
    chord_m: float          # Chord length [m]
    twist_rad: float        # Local twist angle (geometric pitch) [rad]
    cl_alpha: float         # Lift-curve slope [1/rad]
    cd0: float              # Parasitic drag coefficient (zero-lift)

    def __post_init__(self) -> None:
        if self.radius_m <= 0:
            raise ValueError(f"radius_m must be positive, got {self.radius_m}")
        if self.chord_m <= 0:
            raise ValueError(f"chord_m must be positive, got {self.chord_m}")
        if self.cl_alpha <= 0:
            raise ValueError(f"cl_alpha must be positive, got {self.cl_alpha}")
        if self.cd0 < 0:
            raise ValueError(f"cd0 must be >= 0, got {self.cd0}")


@dataclass(frozen=True)
class RotorGeometry:
    """Complete rotor geometry specification."""

    n_blades: int           # Number of blades
    tip_radius_m: float     # Tip radius [m]
    hub_radius_m: float     # Hub radius [m]
    root_chord_m: float     # Root chord [m]
    tip_chord_m: float      # Tip chord (linear taper) [m]
    root_twist_rad: float   # Root twist [rad]
    tip_twist_rad: float    # Tip twist [rad]

    def __post_init__(self) -> None:
        if self.n_blades < 1:
            raise ValueError(f"n_blades must be >= 1, got {self.n_blades}")
        if self.tip_radius_m <= 0:
            raise ValueError(f"tip_radius_m must be positive, got {self.tip_radius_m}")
        if self.hub_radius_m < 0:
            raise ValueError(f"hub_radius_m must be >= 0, got {self.hub_radius_m}")
        if self.hub_radius_m >= self.tip_radius_m:
            raise ValueError("hub_radius_m must be < tip_radius_m")


@dataclass(frozen=True)
class BEMTCondition:
    """Operating condition for a BEMT analysis."""

    rpm: float              # Rotational speed [rev/min]
    climb_speed_ms: float   # Axial climb velocity [m/s] (0 = hover)
    air_density_kg_m3: float  # Air density [kg/m³]

    def __post_init__(self) -> None:
        if self.rpm <= 0:
            raise ValueError(f"rpm must be positive, got {self.rpm}")
        if self.air_density_kg_m3 <= 0:
            raise ValueError(f"air_density_kg_m3 must be positive, got {self.air_density_kg_m3}")

    @property
    def omega_rad_s(self) -> float:
        """Angular velocity [rad/s]."""
        return self.rpm * 2.0 * math.pi / 60.0


@dataclass(frozen=True)
class ElementResult:
    """Aerodynamic loads at a single blade radial station."""

    radius_m: float
    thrust_n: float
    torque_nm: float
    inflow_angle_rad: float
    alpha_rad: float
    cl: float
    cd: float


@dataclass
class BEMTResult:
    """Integrated rotor performance from a BEMT solve."""

    total_thrust_n: float = 0.0
    total_torque_nm: float = 0.0
    total_power_w: float = 0.0
    ct: float = 0.0          # Thrust coefficient
    cq: float = 0.0          # Torque coefficient
    cp: float = 0.0          # Power coefficient
    figure_of_merit: float = 0.0
    disk_loading_pa: float = 0.0
    converged: bool = True
    element_results: list[ElementResult] = field(default_factory=list)


# ── Geometry discretisation ───────────────────────────────────────────────────


def discretize_rotor(
    geom: RotorGeometry,
    cl_alpha: float,
    cd0: float,
    n_stations: int = 40,
) -> list[BladeElement]:
    """Discretise *geom* into *n_stations* blade elements with linear interpolation.

    Args:
        geom:       Rotor geometry specification.
        cl_alpha:   Lift-curve slope [1/rad] (uniform along span).
        cd0:        Parasitic drag coefficient (uniform along span).
        n_stations: Number of radial stations (clamped to [10, 500]).

    Returns:
        List of :class:`BladeElement`, ordered from root to tip.
    """
    n = max(_MIN_STATIONS, min(_MAX_STATIONS, n_stations))
    radii = np.linspace(geom.hub_radius_m, geom.tip_radius_m, n, endpoint=False)
    # Shift to element centres
    dr = (geom.tip_radius_m - geom.hub_radius_m) / n
    radii = radii + 0.5 * dr

    span = geom.tip_radius_m - geom.hub_radius_m
    elements: list[BladeElement] = []
    for r in radii:
        frac = (r - geom.hub_radius_m) / span
        chord = geom.root_chord_m + frac * (geom.tip_chord_m - geom.root_chord_m)
        twist = geom.root_twist_rad + frac * (geom.tip_twist_rad - geom.root_twist_rad)
        elements.append(BladeElement(
            radius_m=float(r),
            chord_m=float(chord),
            twist_rad=float(twist),
            cl_alpha=cl_alpha,
            cd0=cd0,
        ))
    return elements


# ── BEMT solver ───────────────────────────────────────────────────────────────


def solve_bemt(
    elements: list[BladeElement],
    n_blades: int,
    condition: BEMTCondition,
) -> BEMTResult:
    """Solve BEMT for a given blade discretisation and operating condition.

    Iterates on each element independently to find the induced inflow ratio λ
    that satisfies both momentum theory and blade element theory simultaneously.
    Uses under-relaxation to prevent oscillation.

    Args:
        elements:  Blade elements from :func:`discretize_rotor`.
        n_blades:  Number of blades.
        condition: Operating condition (RPM, climb, density).

    Returns:
        :class:`BEMTResult` with integrated rotor performance.
    """
    omega = condition.omega_rad_s
    rho = condition.air_density_kg_m3
    v_c = condition.climb_speed_ms
    b = n_blades

    tip_radius = elements[-1].radius_m
    disk_area = math.pi * tip_radius ** 2

    total_thrust = 0.0
    total_torque = 0.0
    element_results: list[ElementResult] = []
    all_converged = True

    for elem in elements:
        r = elem.radius_m
        dr = tip_radius / len(elements)  # approximate element width
        sigma_local = b * elem.chord_m / (math.pi * r)  # local solidity

        # Initial guess: momentum-theory inflow ratio
        lam = math.sqrt(sigma_local * elem.cl_alpha / 16.0) - v_c / (omega * tip_radius)
        lam = max(lam, 1e-4)

        converged = False
        for _ in range(_BEMT_MAX_ITER):
            ut = omega * r                              # tangential velocity
            up = omega * tip_radius * lam + v_c        # axial (inflow) velocity
            v_total = math.sqrt(ut ** 2 + up ** 2)

            inflow_angle = math.atan2(up, ut)
            alpha = elem.twist_rad - inflow_angle

            cl = elem.cl_alpha * alpha
            cd = elem.cd0 + 0.01 * cl ** 2  # simple quadratic polar

            # Blade-element thrust per unit span (computed via momentum theory below)

            # Momentum theory: d_thrust = 4 * rho * pi * r * dr * (omega*r_tip) * lam * (lam + v_c/(omega*r_tip))
            v_tip = omega * tip_radius
            lam_new = math.sqrt(
                max(0.0, (sigma_local * elem.cl_alpha / 8.0) * alpha - v_c / (2.0 * v_tip))
            )
            # Clamp to reasonable range
            lam_new = max(1e-4, min(1.0, lam_new))

            delta = lam_new - lam
            lam = lam + _BEMT_RELAX * delta

            if abs(delta) < _BEMT_TOLERANCE:
                converged = True
                break

        if not converged:
            all_converged = False

        # Final aerodynamic loads at this station
        ut = omega * r
        up = omega * tip_radius * lam + v_c
        v_total = math.sqrt(ut ** 2 + up ** 2)
        inflow_angle = math.atan2(up, ut)
        alpha = elem.twist_rad - inflow_angle
        cl = elem.cl_alpha * alpha
        cd = elem.cd0 + 0.01 * cl ** 2

        dL = 0.5 * rho * v_total ** 2 * elem.chord_m * cl * dr
        dD = 0.5 * rho * v_total ** 2 * elem.chord_m * cd * dr

        d_thrust = b * (dL * math.cos(inflow_angle) - dD * math.sin(inflow_angle))
        d_torque = b * r * (dD * math.cos(inflow_angle) + dL * math.sin(inflow_angle))

        total_thrust += d_thrust
        total_torque += d_torque

        element_results.append(ElementResult(
            radius_m=r,
            thrust_n=d_thrust,
            torque_nm=d_torque,
            inflow_angle_rad=inflow_angle,
            alpha_rad=alpha,
            cl=cl,
            cd=cd,
        ))

    total_power = total_torque * omega
    v_tip = omega * tip_radius
    denom_ct = rho * disk_area * v_tip ** 2
    denom_cp = rho * disk_area * v_tip ** 3

    ct = total_thrust / denom_ct if denom_ct > 0 else 0.0
    cp = total_power / denom_cp if denom_cp > 0 else 0.0
    cq = total_torque / (rho * disk_area * tip_radius * v_tip ** 2) if denom_ct > 0 else 0.0

    # Figure of merit: ideal power / actual power (hover only, v_c ≈ 0)
    if total_power > 0 and total_thrust > 0:
        p_ideal = total_thrust * math.sqrt(total_thrust / (2.0 * rho * disk_area))
        figure_of_merit = p_ideal / total_power
    else:
        figure_of_merit = 0.0

    disk_loading = total_thrust / disk_area if disk_area > 0 else 0.0

    return BEMTResult(
        total_thrust_n=total_thrust,
        total_torque_nm=total_torque,
        total_power_w=total_power,
        ct=ct,
        cq=cq,
        cp=cp,
        figure_of_merit=figure_of_merit,
        disk_loading_pa=disk_loading,
        converged=all_converged,
        element_results=element_results,
    )


# ── Convenience helpers ───────────────────────────────────────────────────────


def hover_thrust(
    geom: RotorGeometry,
    rpm: float,
    air_density_kg_m3: float = 1.225,
    cl_alpha: float = 5.73,
    cd0: float = 0.01,
    n_stations: int = 40,
) -> float:
    """Return hover thrust [N] for *geom* at *rpm*.

    Args:
        geom:               Rotor geometry.
        rpm:                Rotational speed [rev/min].
        air_density_kg_m3:  Air density (default ISA sea level).
        cl_alpha:           Lift-curve slope [1/rad].
        cd0:                Parasitic drag coefficient.
        n_stations:         Radial discretisation stations.
    """
    elements = discretize_rotor(geom, cl_alpha=cl_alpha, cd0=cd0, n_stations=n_stations)
    cond = BEMTCondition(
        rpm=rpm,
        climb_speed_ms=0.0,
        air_density_kg_m3=air_density_kg_m3,
    )
    result = solve_bemt(elements, n_blades=geom.n_blades, condition=cond)
    return result.total_thrust_n


def compute_rotor_efficiency(
    geom: RotorGeometry,
    rpm: float,
    air_density_kg_m3: float = 1.225,
    cl_alpha: float = 5.73,
    cd0: float = 0.01,
    n_stations: int = 40,
) -> dict[str, float]:
    """Return a summary dictionary of rotor performance metrics.

    Keys: ``thrust_n``, ``power_w``, ``figure_of_merit``,
          ``disk_loading_pa``, ``ct``, ``cp``.
    """
    elements = discretize_rotor(geom, cl_alpha=cl_alpha, cd0=cd0, n_stations=n_stations)
    cond = BEMTCondition(
        rpm=rpm,
        climb_speed_ms=0.0,
        air_density_kg_m3=air_density_kg_m3,
    )
    r = solve_bemt(elements, n_blades=geom.n_blades, condition=cond)
    return {
        "thrust_n": r.total_thrust_n,
        "power_w": r.total_power_w,
        "figure_of_merit": r.figure_of_merit,
        "disk_loading_pa": r.disk_loading_pa,
        "ct": r.ct,
        "cp": r.cp,
    }

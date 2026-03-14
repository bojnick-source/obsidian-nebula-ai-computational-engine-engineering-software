"""REIDCE — Reid Industries Engineering Design and Computational Engine.

Physics solver library for aerospace and structural analysis.

Submodules
----------
aerospace         ISA atmosphere, lift/drag, range/endurance
bemt              Blade Element Momentum Theory rotor solver
energy_maneuverability  Boyd/Christie E-M analysis
fea               1D Euler-Bernoulli beam FEA
ratio             Ratio string parser/validator
wind_tunnel       Computational wind tunnel (thin-airfoil + lifting-line)
"""
from __future__ import annotations

from reidce.aerospace import (
    AeroCoefficients,
    ISAAtmosphere,
    RangeEstimate,
    estimate_glide_ratio,
    isa_atmosphere,
    lift_drag,
    range_endurance,
    thrust_to_weight,
    wing_loading,
)
from reidce.bemt import (
    BEMTCondition,
    BEMTResult,
    BladeElement,
    ElementResult,
    RotorGeometry,
    compute_rotor_efficiency,
    discretize_rotor,
    hover_thrust,
    solve_bemt,
)
from reidce.energy_maneuverability import (
    Atmosphere,
    EMState,
    StructuralLimits,
    VehicleParams,
    VehicleState,
    compute_drag,
    compute_em_envelope,
    compute_em_state,
    find_sustained_turn_rate,
    load_factor,
    specific_energy,
    specific_excess_power,
    turn_radius,
    turn_rate,
)
from reidce.fea import (
    BeamElement,
    BoundaryCondition,
    ElementStress,
    FEAMesh,
    FEAResult,
    Node,
    NodalResult,
    PointLoad,
    cantilever_fea,
    generate_beam_mesh,
    solve_static,
)
from reidce.ratio import (
    RatioResult,
    parse_ratio,
)
from reidce.wind_tunnel import (
    AeroResult,
    AirfoilGeometry,
    ConvergenceMetrics,
    DrydenGust,
    FlowCondition,
    WindTunnelResult,
    WindTunnelSweepPoint,
    compute_aero,
    dryden_gust_velocities,
    interpolate_aero,
    run_wind_tunnel,
)

__all__ = [
    # aerospace
    "AeroCoefficients",
    "ISAAtmosphere",
    "RangeEstimate",
    "estimate_glide_ratio",
    "isa_atmosphere",
    "lift_drag",
    "range_endurance",
    "thrust_to_weight",
    "wing_loading",
    # bemt
    "BEMTCondition",
    "BEMTResult",
    "BladeElement",
    "ElementResult",
    "RotorGeometry",
    "compute_rotor_efficiency",
    "discretize_rotor",
    "hover_thrust",
    "solve_bemt",
    # energy_maneuverability
    "Atmosphere",
    "EMState",
    "StructuralLimits",
    "VehicleParams",
    "VehicleState",
    "compute_drag",
    "compute_em_envelope",
    "compute_em_state",
    "find_sustained_turn_rate",
    "load_factor",
    "specific_energy",
    "specific_excess_power",
    "turn_radius",
    "turn_rate",
    # fea
    "BeamElement",
    "BoundaryCondition",
    "ElementStress",
    "FEAMesh",
    "FEAResult",
    "Node",
    "NodalResult",
    "PointLoad",
    "cantilever_fea",
    "generate_beam_mesh",
    "solve_static",
    # ratio
    "RatioResult",
    "parse_ratio",
    # wind_tunnel
    "AeroResult",
    "AirfoilGeometry",
    "ConvergenceMetrics",
    "DrydenGust",
    "FlowCondition",
    "WindTunnelResult",
    "WindTunnelSweepPoint",
    "compute_aero",
    "dryden_gust_velocities",
    "interpolate_aero",
    "run_wind_tunnel",
]

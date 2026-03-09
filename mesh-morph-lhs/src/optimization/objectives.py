"""Objective functions for multi-criteria scoring of evaluated candidates.

Primary objectives (used for Pareto sorting):
    compliance  — structural stiffness (lower = stiffer)
    mass        — total truss mass (lower = lighter)

Secondary penalties (folded into scalar aggregate):
    stress_penalty  — penalty for member stresses exceeding the yield fraction
    mesh_penalty    — from mesh quality assessment

Scalar aggregate (for ranking when Pareto front is ambiguous):
    J = w_c * compliance_norm
      + w_m * mass_norm
      + w_s * stress_penalty
      + w_q * mesh_penalty
"""

from __future__ import annotations

import numpy as np

from ..simulation.solver import SolverResult
from ..simulation.structural_model import StructuralState


def compute_objectives(
    state: StructuralState,
    result: SolverResult,
    quality: dict,
    scoring_cfg: dict,
) -> dict:
    """Compute all objective values for one evaluated candidate.

    Parameters
    ----------
    state:
        StructuralState providing material properties (yield stress) and mass.
    result:
        Converged SolverResult.
    quality:
        Mesh quality dict from mesh_quality.compute_quality().
    scoring_cfg:
        The ``scoring`` section of design_space.yaml (weights + stress_limit_fraction).

    Returns
    -------
    dict with keys: compliance, mass, max_stress, max_displacement,
    stress_penalty, mesh_penalty, strain_energy
    """
    compliance = float(result.compliance)
    mass = state.total_mass()
    max_stress = float(result.max_stress)
    max_disp = float(result.max_displacement)
    mesh_penalty = float(quality.get("mesh_penalty", 0.0))

    # Stress penalty: ramps up once |stress| exceeds threshold fraction of yield
    sigma_limit = (
        float(scoring_cfg.get("stress_limit_fraction", 0.8))
        * state.material.yield_stress
    )
    stress_excess = float(np.maximum(0.0, max_stress - sigma_limit))
    # Normalise by yield stress so the penalty is dimensionless
    stress_penalty = (stress_excess / state.material.yield_stress) ** 2

    return {
        "compliance": compliance,
        "mass": mass,
        "max_stress": max_stress,
        "max_displacement": max_disp,
        "stress_penalty": stress_penalty,
        "mesh_penalty": mesh_penalty,
        "strain_energy": compliance,   # for elastic trusses, compliance = 2 × strain energy
    }


def aggregate_score(objectives: dict, scoring_cfg: dict) -> float:
    """Compute scalar aggregate score J from objectives dict and weights.

    Before weighting, compliance and mass are raw physical values.
    They are normalised internally to [0,1] using soft normalisation
    (division by a reference value based on the values themselves).
    This avoids unit dependency and keeps all penalty terms on a similar scale.
    """
    w_c = float(scoring_cfg.get("w_compliance", 1.0))
    w_m = float(scoring_cfg.get("w_mass", 0.5))
    w_s = float(scoring_cfg.get("w_stress_penalty", 2.0))
    w_q = float(scoring_cfg.get("w_mesh_penalty", 0.3))

    # Soft normalisation: divide by (1 + value) so large values stay finite
    compliance_norm = objectives["compliance"] / (1.0 + abs(objectives["compliance"]))
    mass_norm = objectives["mass"] / (1.0 + objectives["mass"])

    J = (
        w_c * compliance_norm
        + w_m * mass_norm
        + w_s * objectives["stress_penalty"]
        + w_q * (objectives["mesh_penalty"] / (1.0 + objectives["mesh_penalty"]))
    )
    return float(J)


def normalise_objective_archive(archive: list[dict], key: str) -> np.ndarray:
    """Return normalised (0-1) values of a named objective across the archive.

    Uses min-max normalisation. Used by the Pareto sorter for comparisons.
    """
    values = np.array([r["objectives"][key] for r in archive if "objectives" in r])
    v_min, v_max = np.min(values), np.max(values)
    if v_max - v_min < 1e-12:
        return np.zeros_like(values)
    return (values - v_min) / (v_max - v_min)

"""Hard constraint evaluation for candidate rejection.

Candidates that violate hard constraints are given score = inf and
excluded from surrogate training and Pareto analysis.
"""

from __future__ import annotations

import numpy as np

from ..geometry.parametric_mesh import MorphedMesh
from ..simulation.solver import SolverResult
from ..simulation.structural_model import StructuralState


def check_hard_constraints(
    morphed: MorphedMesh,
    state: StructuralState,
    result: SolverResult,
    cfg: dict,
) -> tuple[bool, str]:
    """Return (is_feasible, reason).

    Evaluated in order; returns on first violation.
    """
    # 1. Mesh quality
    if not morphed.quality["is_valid"]:
        return False, "invalid mesh quality"

    # 2. Topology (connectivity)
    if not morphed.topology["topology_valid"]:
        return False, "invalid topology"

    # 3. Solver convergence
    if not result.converged:
        return False, f"solver failed: {result.reason}"

    # 4. Non-physical displacements
    if result.max_displacement > 1e6:
        return False, "displacement exceeds physical bounds"

    # 5. Stress above hard yield limit (not just the soft penalty threshold)
    yield_stress = state.material.yield_stress
    hard_stress_limit = float(cfg.get("hard_stress_multiplier", 2.0)) * yield_stress
    if result.max_stress > hard_stress_limit:
        return False, f"stress {result.max_stress:.2e} Pa exceeds hard limit {hard_stress_limit:.2e} Pa"

    # 6. Minimum feature size (manufacturing constraint)
    min_edge = morphed.quality["min_edge_length"]
    min_feature = float(cfg.get("min_feature_size", 0.0))
    if min_feature > 0 and min_edge < min_feature:
        return False, f"min edge {min_edge:.4f} < min feature size {min_feature}"

    return True, "ok"


def invalid_result(params: dict, quality: dict, reason: str = "invalid mesh") -> dict:
    """Build a result dict for a candidate that failed constraint checks."""
    return {
        "params": params,
        "mesh": None,
        "objectives": None,
        "score": float("inf"),
        "feasible": False,
        "reason": reason,
        "quality": quality,
        "sim_result": None,
    }


def failed_sim_result(params: dict, quality: dict, sim_reason: str) -> dict:
    """Build a result dict for a candidate where the solver failed."""
    return {
        "params": params,
        "mesh": None,
        "objectives": None,
        "score": float("inf"),
        "feasible": False,
        "reason": sim_reason,
        "quality": quality,
        "sim_result": None,
    }

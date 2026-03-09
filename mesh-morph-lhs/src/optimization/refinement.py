"""Adaptive refinement strategy for multi-generation search.

Provides the population transition logic between generations:
1. Extract elites from the current generation.
2. Fit a surrogate on the full archive.
3. Propose n_samples new candidates (mix of surrogate-guided + LHS).
"""

from __future__ import annotations

import numpy as np

from .ranking import select_elite
from ..sampling.adaptive_sampling import adaptive_resample
from ..sampling.parameter_map import ParameterSpec


def next_population(
    generation_results: list[dict],
    archive: list[dict],
    specs: list[ParameterSpec],
    n_samples: int,
    cfg: dict,
    seed: int | None = None,
) -> np.ndarray:
    """Generate the next generation's sample matrix from the current results.

    Parameters
    ----------
    generation_results:
        Results from the most recent generation (feasible + infeasible).
    archive:
        Cumulative archive of all prior evaluations.
    specs:
        Parameter specifications for normalisation.
    n_samples:
        Total samples to generate for the next generation.
    cfg:
        Full config dict (uses ``optimization`` sub-section).
    seed:
        RNG seed for reproducibility.

    Returns
    -------
    H : (n_samples, n_dim) array in [0, 1]^n_dim
    """
    opt_cfg = cfg.get("optimization", {})
    elite_fraction = float(opt_cfg.get("elite_fraction", 0.20))
    resample_fraction = float(opt_cfg.get("resample_fraction", 0.80))

    return adaptive_resample(
        archive=archive,
        specs=specs,
        n_samples=n_samples,
        elite_fraction=elite_fraction,
        resample_fraction=resample_fraction,
        seed=seed,
    )


def convergence_check(archive: list[dict], window: int = 3, tol: float = 0.01) -> bool:
    """Return True if the best score has not improved by more than tol in the
    last *window* generations worth of feasible evaluations.

    This is a simple stall-detection heuristic, not a formal convergence test.
    """
    feasible = sorted(
        [r for r in archive if r.get("feasible")],
        key=lambda r: r.get("score", float("inf")),
    )
    if len(feasible) < window * 2:
        return False

    recent_best = feasible[0]["score"]
    older_best = feasible[window]["score"]

    rel_improvement = abs(older_best - recent_best) / (abs(older_best) + 1e-12)
    return rel_improvement < tol

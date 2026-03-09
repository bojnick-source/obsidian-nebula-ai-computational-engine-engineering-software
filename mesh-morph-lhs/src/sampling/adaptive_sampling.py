"""Adaptive resampling around high-performing elite candidates.

After each generation the archive is used to:
1. Fit an RBF surrogate on (normalised_params, score).
2. Propose new candidates from predicted low-score regions.
3. Mix surrogate-guided proposals with random LHS for exploration.

The result is a new (n_samples, n_dim) unit-interval sample matrix.
"""

from __future__ import annotations

import numpy as np

from .lhs import lhs, lhs_augment
from .parameter_map import ParameterSpec, normalise_archive
from ..simulation.surrogate_model import ScoreSurrogate


def adaptive_resample(
    archive: list[dict],
    specs: list[ParameterSpec],
    n_samples: int,
    elite_fraction: float = 0.20,
    resample_fraction: float = 0.70,
    seed: int | None = None,
) -> np.ndarray:
    """Generate a new sample matrix informed by the archive of evaluations.

    Parameters
    ----------
    archive:
        List of result dicts. Each must have ``"params"`` and ``"score"``
        keys. Invalid/failed entries with ``score = inf`` are allowed —
        they are excluded from the surrogate fit but the elite selection
        may still use them if valid alternatives are scarce.
    specs:
        Parameter specs (used for normalisation and bounds).
    n_samples:
        Total number of new samples to generate.
    elite_fraction:
        Fraction of valid archive entries used as "elites" for local mutation.
    resample_fraction:
        Fraction of new population generated from surrogate guidance.
        The rest (``1 - resample_fraction``) comes from global LHS.
    seed:
        Optional RNG seed for reproducibility.

    Returns
    -------
    H : (n_samples, n_dim) array in [0, 1]^n_dim
    """
    rng = np.random.default_rng(seed)
    n_dim = len(specs)
    n_surrogate = int(n_samples * resample_fraction)
    n_global = n_samples - n_surrogate

    # ── Normalise valid archive entries ───────────────────────────────────────
    valid = [r for r in archive if np.isfinite(r.get("score", float("inf")))]

    if len(valid) < 3:
        # Not enough data — fall back to pure LHS
        return lhs(n_samples, n_dim, seed=rng.integers(0, 2**31), maximin_iters=50)

    X_all = normalise_archive(valid, specs)
    y_all = np.array([r["score"] for r in valid])

    # ── Identify elites ───────────────────────────────────────────────────────
    n_elite = max(1, int(len(valid) * elite_fraction))
    elite_idx = np.argsort(y_all)[:n_elite]
    X_elite = X_all[elite_idx]

    # ── Fit surrogate ─────────────────────────────────────────────────────────
    surrogate = ScoreSurrogate()
    surrogate.fit(X_all, y_all)

    # ── Surrogate-guided proposals ────────────────────────────────────────────
    if surrogate.is_fitted:
        n_surr_pool = max(n_surrogate * 3, 300)
        # Mix: local Gaussian perturbation of elites + uniform random pool
        local = _local_perturbation(X_elite, n_surr_pool // 2, rng)
        uniform_pool = rng.random((n_surr_pool - len(local), n_dim))
        pool = np.vstack([local, uniform_pool])
        predicted = surrogate.predict(pool)
        top_idx = np.argsort(predicted)[:n_surrogate]
        H_surrogate = pool[top_idx]
    else:
        H_surrogate = lhs_augment(X_elite, n_surrogate, n_dim, rng)

    # ── Global LHS for diversity ──────────────────────────────────────────────
    if n_global > 0:
        existing = np.vstack([X_all, H_surrogate])
        H_global = lhs_augment(existing, n_global, n_dim, rng)
    else:
        H_global = np.empty((0, n_dim))

    H = np.vstack([H_surrogate, H_global]) if n_global > 0 else H_surrogate
    # Clip to [0,1] (Gaussian perturbation can push out of bounds)
    return np.clip(H[:n_samples], 0.0, 1.0)


def _local_perturbation(
    X_elite: np.ndarray,
    n_out: int,
    rng: np.random.Generator,
    sigma: float = 0.15,
) -> np.ndarray:
    """Generate local perturbations around elite candidates."""
    if len(X_elite) == 0:
        return np.empty((0, X_elite.shape[1] if X_elite.ndim > 1 else 1))
    idx = rng.integers(0, len(X_elite), size=n_out)
    noise = rng.normal(0, sigma, size=(n_out, X_elite.shape[1]))
    return np.clip(X_elite[idx] + noise, 0.0, 1.0)

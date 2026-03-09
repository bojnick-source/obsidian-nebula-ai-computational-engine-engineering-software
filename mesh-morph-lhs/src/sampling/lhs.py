"""Latin Hypercube Sampling with optional maximin criterion.

The basic permutation LHS guarantees one sample per stratum in each
dimension. The maximin criterion selects the design with the largest
minimum pairwise distance — providing better coverage of the design space.
"""

from __future__ import annotations

import numpy as np


def lhs_basic(n_samples: int, n_dim: int, rng: np.random.Generator) -> np.ndarray:
    """Single permutation-LHS design in [0,1]^n_dim.

    Returns (n_samples, n_dim) array.
    """
    H = np.zeros((n_samples, n_dim))
    for d in range(n_dim):
        perm = rng.permutation(n_samples)
        H[:, d] = (perm + rng.random(n_samples)) / n_samples
    return H


def min_pairwise_distance(H: np.ndarray) -> float:
    """Minimum Euclidean distance between any pair of rows in H."""
    if len(H) < 2:
        return float("inf")
    best = float("inf")
    for i in range(len(H)):
        diffs = H[i + 1 :] - H[i]
        dists = np.linalg.norm(diffs, axis=1)
        if len(dists):
            best = min(best, float(np.min(dists)))
    return best


def lhs(
    n_samples: int,
    n_dim: int,
    seed: int | None = None,
    maximin_iters: int = 0,
) -> np.ndarray:
    """Generate a Latin Hypercube Sample in [0,1]^n_dim.

    Parameters
    ----------
    n_samples:
        Number of design points.
    n_dim:
        Number of design variables.
    seed:
        Random seed for reproducibility.
    maximin_iters:
        If > 0, generate this many candidate LHS designs and keep the one
        with the largest minimum pairwise distance (maximin criterion).

    Returns
    -------
    H : (n_samples, n_dim) float array
    """
    rng = np.random.default_rng(seed)
    best_H = lhs_basic(n_samples, n_dim, rng)

    if maximin_iters > 0:
        best_dist = min_pairwise_distance(best_H)
        for _ in range(maximin_iters - 1):
            candidate = lhs_basic(n_samples, n_dim, rng)
            d = min_pairwise_distance(candidate)
            if d > best_dist:
                best_dist = d
                best_H = candidate

    return best_H


def lhs_augment(
    existing: np.ndarray,
    n_new: int,
    n_dim: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate n_new new points that avoid existing sample locations.

    Uses a greedy maximin approach: repeatedly propose random points and
    keep those maximally distant from the existing set.
    """
    pool_size = max(n_new * 20, 200)
    pool = rng.random((pool_size, n_dim))

    chosen: list[np.ndarray] = []
    current = existing.copy()

    for _ in range(n_new):
        # Compute minimum distance of each pool point to current set
        if len(current) == 0:
            idx = 0
        else:
            dists_to_current = np.min(
                np.linalg.norm(pool[:, None, :] - current[None, :, :], axis=2),
                axis=1,
            )
            idx = int(np.argmax(dists_to_current))

        chosen.append(pool[idx])
        current = np.vstack([current, pool[idx]])
        pool = np.delete(pool, idx, axis=0)
        if len(pool) == 0:
            break

    return np.array(chosen)

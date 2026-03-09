"""General mathematical utilities for the morphogenesis engine."""

from __future__ import annotations

import numpy as np


def safe_divide(a: float | np.ndarray, b: float | np.ndarray, default: float = 0.0) -> float | np.ndarray:
    """Divide a by b, returning default where b is near zero."""
    scalar = np.isscalar(a) and np.isscalar(b)
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    mask = np.abs(b_arr) < 1e-300
    result = np.where(mask, default, a_arr / np.where(mask, 1.0, b_arr))
    return float(result) if scalar else result


def normalise_rows(X: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Normalise each row of X to unit L2 norm."""
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    return X / (norms + eps)


def unit_range(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Scale v to [0, 1] using min-max normalisation."""
    v_min, v_max = np.min(v), np.max(v)
    return (v - v_min) / max(v_max - v_min, eps)


def min_pairwise_dist_sq(X: np.ndarray) -> float:
    """Minimum squared Euclidean distance between any two rows of X."""
    n = len(X)
    if n < 2:
        return float("inf")
    best = float("inf")
    for i in range(n):
        diff = X[i + 1:] - X[i]
        dists_sq = np.sum(diff ** 2, axis=1)
        if len(dists_sq):
            best = min(best, float(np.min(dists_sq)))
    return best


def cartesian_to_cylindrical(v: np.ndarray) -> np.ndarray:
    """Convert (N,3) cartesian XYZ to (N,3) cylindrical (r, theta, z)."""
    r = np.linalg.norm(v[:, :2], axis=1)
    theta = np.arctan2(v[:, 1], v[:, 0])
    return np.column_stack([r, theta, v[:, 2]])


def rotation_matrix_z(angle_deg: float) -> np.ndarray:
    """3×3 rotation matrix about the Z-axis."""
    t = np.deg2rad(angle_deg)
    return np.array([
        [np.cos(t), -np.sin(t), 0.0],
        [np.sin(t),  np.cos(t), 0.0],
        [0.0,        0.0,       1.0],
    ])


def centroid(v: np.ndarray) -> np.ndarray:
    """Return the centroid of a (N,3) vertex array."""
    return np.mean(v, axis=0)

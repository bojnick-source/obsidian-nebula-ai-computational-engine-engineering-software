"""Mesh quality metrics for structural-analysis suitability.

All functions operate on MeshState and return plain dicts so results
can be serialised directly to JSON.
"""

from __future__ import annotations

import numpy as np

from .base_mesh import MeshState


def edge_lengths(mesh: MeshState) -> np.ndarray:
    """Return (E,) array of member lengths."""
    v = mesh.vertices
    e = mesh.edges
    return np.linalg.norm(v[e[:, 1]] - v[e[:, 0]], axis=1)


def compute_quality(mesh: MeshState, min_len_tol: float = 1e-3) -> dict:
    """Compute mesh quality metrics and return as a flat dict.

    Keys
    ----
    is_valid :
        True iff min_edge_length >= min_len_tol and no isolated nodes
    min_edge_length : float
    max_edge_length : float
    mean_edge_length : float
    length_ratio : float  — max/min edge length (aspect ratio proxy)
    quality_score : float in [0, 1]  — 1 = perfect, 0 = degenerate
    mesh_penalty : float  — penalty term for use in objective function
    n_degenerate_edges : int
    """
    lens = edge_lengths(mesh)

    if len(lens) == 0:
        return _invalid_quality("no edges")

    min_len = float(np.min(lens))
    max_len = float(np.max(lens))
    mean_len = float(np.mean(lens))

    n_deg = int(np.sum(lens < min_len_tol))
    is_valid = n_deg == 0

    # Aspect ratio: ratio of longest to shortest member
    ratio = max_len / max(min_len, min_len_tol)

    # Quality score: exponentially penalises high aspect ratios
    # q=1 for ratio=1; decays toward 0 as ratio grows
    quality_score = float(np.exp(-0.1 * (ratio - 1.0)))
    quality_score = np.clip(quality_score, 0.0, 1.0)

    # Mesh penalty: additive term for the objective function
    mesh_penalty = max(0.0, ratio - 5.0) * 0.1 + n_deg * 100.0

    # Check for isolated nodes (nodes not connected to any edge)
    connected_nodes = set(mesh.edges.ravel())
    n_isolated = mesh.n_nodes - len(connected_nodes)
    if n_isolated > 0:
        is_valid = False
        mesh_penalty += n_isolated * 50.0

    return {
        "is_valid": is_valid,
        "min_edge_length": min_len,
        "max_edge_length": max_len,
        "mean_edge_length": mean_len,
        "length_ratio": float(ratio),
        "quality_score": quality_score,
        "mesh_penalty": mesh_penalty,
        "n_degenerate_edges": n_deg,
        "n_isolated_nodes": n_isolated,
    }


def _invalid_quality(reason: str) -> dict:
    return {
        "is_valid": False,
        "min_edge_length": 0.0,
        "max_edge_length": 0.0,
        "mean_edge_length": 0.0,
        "length_ratio": float("inf"),
        "quality_score": 0.0,
        "mesh_penalty": 1e6,
        "n_degenerate_edges": 0,
        "n_isolated_nodes": 0,
        "reason": reason,
    }


def laplacian_adjacency(mesh: MeshState) -> list[list[int]]:
    """Build adjacency list for Laplacian operations."""
    n = mesh.n_nodes
    adj: list[list[int]] = [[] for _ in range(n)]
    for a, b in mesh.edges:
        adj[a].append(int(b))
        adj[b].append(int(a))
    return adj

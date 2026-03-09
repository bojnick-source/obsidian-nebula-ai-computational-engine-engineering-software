"""Composable morph operators applied sequentially to a MeshState.

Each operator is a pure function:
    (MeshState, params: dict) -> MeshState

The canonical pipeline is:
    base_mesh
    → apply_span_scale
    → apply_height_scale
    → apply_curvature
    → apply_twist
    → apply_cell_skew
    → apply_branch_bias
    → apply_laplacian_smooth
    → clamp_min_edge_length   (safety)

All operators operate on a copy of the vertex array and leave the edge/face
connectivity unchanged.
"""

from __future__ import annotations

import numpy as np

from .base_mesh import MeshState


# ── Individual operators ─────────────────────────────────────────────────────

def apply_span_scale(mesh: MeshState, params: dict) -> MeshState:
    """Uniform stretch along X-axis."""
    v = mesh.vertices.copy()
    v[:, 0] *= params.get("span_scale", 1.0)
    return mesh.copy_with_vertices(v)


def apply_height_scale(mesh: MeshState, params: dict) -> MeshState:
    """Uniform stretch along Y-axis."""
    v = mesh.vertices.copy()
    v[:, 1] *= params.get("height_scale", 1.0)
    return mesh.copy_with_vertices(v)


def apply_curvature(mesh: MeshState, params: dict) -> MeshState:
    """Sinusoidal Z-displacement — injects 3D curvature into a planar lattice.

    Uses normalised coordinates so the frequency adapts to mesh extent.
    """
    v = mesh.vertices.copy()
    amp = params.get("curvature_amp", 0.0)
    density = params.get("lattice_density", 4.0)

    if abs(amp) < 1e-9:
        return mesh.copy_with_vertices(v)

    x_range = np.ptp(v[:, 0]) or 1.0
    y_range = np.ptp(v[:, 1]) or 1.0
    x_norm = (v[:, 0] - np.min(v[:, 0])) / x_range
    y_norm = (v[:, 1] - np.min(v[:, 1])) / y_range

    freq = np.pi * density / 4.0
    dz = amp * np.sin(freq * x_norm) * np.cos(freq * y_norm)
    v[:, 2] += dz
    return mesh.copy_with_vertices(v)


def apply_twist(mesh: MeshState, params: dict) -> MeshState:
    """Progressive rotation about Z-axis proportional to Y coordinate.

    Simulates a twisted lattice — twist angle max at the top edge.
    """
    v = mesh.vertices.copy()
    angle_deg = params.get("twist_angle", 0.0)
    if abs(angle_deg) < 1e-9:
        return mesh.copy_with_vertices(v)

    y_min, y_max = np.min(v[:, 1]), np.max(v[:, 1])
    y_range = y_max - y_min or 1.0
    t = (v[:, 1] - y_min) / y_range  # 0 at bottom, 1 at top

    cx = np.mean(v[:, 0])
    cy = np.mean(v[:, 1])
    dx = v[:, 0] - cx
    dy = v[:, 1] - cy
    theta = np.deg2rad(angle_deg) * t
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    v[:, 0] = cx + cos_t * dx - sin_t * dy
    v[:, 1] = cy + sin_t * dx + cos_t * dy
    return mesh.copy_with_vertices(v)


def apply_cell_skew(mesh: MeshState, params: dict) -> MeshState:
    """Shear-like X-displacement proportional to Y — tilts the lattice."""
    v = mesh.vertices.copy()
    skew = params.get("cell_skew", 0.0)
    if abs(skew) < 1e-9:
        return mesh.copy_with_vertices(v)

    y_range = np.ptp(v[:, 1]) or 1.0
    v[:, 0] += skew * (v[:, 1] - np.min(v[:, 1])) / y_range * y_range
    return mesh.copy_with_vertices(v)


def apply_branch_bias(mesh: MeshState, params: dict) -> MeshState:
    """Asymmetric X-stretch: nodes above mid-height shifted toward +/- X.

    Simulates branching geometry where the upper half fans out (positive bias)
    or converges (negative bias).
    """
    v = mesh.vertices.copy()
    bias = params.get("branch_bias", 0.0)
    if abs(bias) < 1e-9:
        return mesh.copy_with_vertices(v)

    y_mid = np.mean(v[:, 1])
    above = v[:, 1] > y_mid
    x_range = np.ptp(v[:, 0]) or 1.0
    cx = np.mean(v[:, 0])
    v[above, 0] += bias * (v[above, 0] - cx) / x_range * x_range * 0.3
    return mesh.copy_with_vertices(v)


def apply_laplacian_smooth(mesh: MeshState, params: dict, iterations: int = 3) -> MeshState:
    """Umbrella-operator Laplacian smoothing on Z coordinate only.

    Preserves XY layout; smooths the curvature injection to reduce
    sharp wrinkles that would cause poor mesh quality.
    """
    strength = params.get("smoothing_strength", 0.0)
    if strength < 1e-9:
        return mesh

    v = mesh.vertices.copy()
    n = len(v)

    # Build adjacency list from edge connectivity
    adj: list[list[int]] = [[] for _ in range(n)]
    for a, b in mesh.edges:
        adj[a].append(b)
        adj[b].append(a)

    lam = strength * 0.5  # per-iteration blend factor
    for _ in range(iterations):
        z_new = v[:, 2].copy()
        for i in range(n):
            nb = adj[i]
            if nb:
                z_new[i] = (1.0 - lam) * v[i, 2] + lam * np.mean(v[nb, 2])
        v[:, 2] = z_new

    return mesh.copy_with_vertices(v)


# ── Safety clamp ─────────────────────────────────────────────────────────────

def clamp_min_edge_length(mesh: MeshState, min_len: float = 1e-3) -> MeshState:
    """If any edge is shorter than min_len, collapse it toward the midpoint.

    This is a conservative repair — it slightly relocates one endpoint.
    Used as the final step to guarantee solver-valid geometry.
    """
    v = mesh.vertices.copy()
    edges = mesh.edges
    for a, b in edges:
        diff = v[b] - v[a]
        L = np.linalg.norm(diff)
        if L < min_len and L > 0:
            mid = 0.5 * (v[a] + v[b])
            half = 0.5 * min_len * diff / L
            v[a] = mid - half
            v[b] = mid + half
    return mesh.copy_with_vertices(v)


# ── Full pipeline ─────────────────────────────────────────────────────────────

PIPELINE: list = [
    apply_span_scale,
    apply_height_scale,
    apply_curvature,
    apply_twist,
    apply_cell_skew,
    apply_branch_bias,
    apply_laplacian_smooth,
]


def morph_mesh(base: MeshState, params: dict) -> MeshState:
    """Apply the full morph pipeline and return the morphed MeshState.

    The base mesh is never mutated.
    """
    mesh = base.copy()
    for op in PIPELINE:
        mesh = op(mesh, params)
    mesh = clamp_min_edge_length(mesh)
    mesh.metadata["params"] = params
    return mesh


# ── Patch MeshState with helper ───────────────────────────────────────────────

def _copy_with_vertices(self: MeshState, v: np.ndarray) -> MeshState:
    return MeshState(
        vertices=v,
        edges=self.edges.copy(),
        faces=self.faces.copy() if self.faces is not None else None,
        metadata=dict(self.metadata),
    )


# Monkey-patch the convenience method onto MeshState
MeshState.copy_with_vertices = _copy_with_vertices  # type: ignore[attr-defined]

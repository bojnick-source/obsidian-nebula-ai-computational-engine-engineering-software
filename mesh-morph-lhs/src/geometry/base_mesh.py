"""Base mesh definitions and factory functions.

Provides the canonical MeshState dataclass and builders for common
lattice topologies used as starting points for morphing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class MeshState:
    """Lightweight mesh representation sufficient for truss/lattice analysis.

    Attributes
    ----------
    vertices:
        (N, 3) float array of node coordinates in global space.
    edges:
        (E, 2) int array of node-index pairs defining structural members.
    faces:
        Optional (F, 3|4) int array of face connectivity.
    metadata:
        Arbitrary key-value store for provenance and per-sample annotations.
    """

    vertices: np.ndarray            # (N, 3)
    edges: np.ndarray               # (E, 2)
    faces: np.ndarray | None = None # (F, k) optional
    metadata: dict = field(default_factory=dict)

    @property
    def n_nodes(self) -> int:
        return len(self.vertices)

    @property
    def n_edges(self) -> int:
        return len(self.edges)

    def copy(self) -> "MeshState":
        return MeshState(
            vertices=self.vertices.copy(),
            edges=self.edges.copy(),
            faces=self.faces.copy() if self.faces is not None else None,
            metadata=dict(self.metadata),
        )

    def node_index(self, i: int, j: int, nx: int) -> int:
        """Helper: flat index for a grid node at column i, row j."""
        return j * nx + i


def make_grid_mesh(
    nx: int = 8,
    ny: int = 8,
    spacing: float = 1.0,
    diagonals: bool = True,
    nz: int = 1,
) -> MeshState:
    """Structured rectangular grid lattice.

    Parameters
    ----------
    nx, ny:
        Number of nodes along x and y axes.
    spacing:
        Uniform node spacing.
    diagonals:
        If True, add cross-diagonal edges on each grid cell for shear stiffness.
    nz:
        Layers in z. nz=1 gives a planar 2.5D mesh; nz>1 gives a 3D lattice.
    """
    verts: list[list[float]] = []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                verts.append([i * spacing, j * spacing, k * spacing])
    vertices = np.array(verts, dtype=float)

    def idx(i: int, j: int, k: int = 0) -> int:
        return k * (nx * ny) + j * nx + i

    edges: list[list[int]] = []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                # X-direction edges
                if i < nx - 1:
                    edges.append([idx(i, j, k), idx(i + 1, j, k)])
                # Y-direction edges
                if j < ny - 1:
                    edges.append([idx(i, j, k), idx(i, j + 1, k)])
                # Z-direction edges (if 3D)
                if nz > 1 and k < nz - 1:
                    edges.append([idx(i, j, k), idx(i, j, k + 1)])
                # Face diagonals (XY plane)
                if diagonals and i < nx - 1 and j < ny - 1:
                    edges.append([idx(i, j, k), idx(i + 1, j + 1, k)])
                    edges.append([idx(i + 1, j, k), idx(i, j + 1, k)])
                # XZ face diagonals
                if diagonals and nz > 1 and i < nx - 1 and k < nz - 1:
                    edges.append([idx(i, j, k), idx(i + 1, j, k + 1)])
                    edges.append([idx(i + 1, j, k), idx(i, j, k + 1)])
                # YZ face diagonals
                if diagonals and nz > 1 and j < ny - 1 and k < nz - 1:
                    edges.append([idx(i, j, k), idx(i, j + 1, k + 1)])
                    edges.append([idx(i, j + 1, k), idx(i, j, k + 1)])

    return MeshState(
        vertices=vertices,
        edges=np.array(edges, dtype=int),
        metadata={"type": "grid", "nx": nx, "ny": ny, "nz": nz, "spacing": spacing},
    )


def make_hex_mesh(rings: int = 3, spacing: float = 1.0) -> MeshState:
    """Hexagonal/honeycomb-pattern lattice in the XY plane."""
    from collections import defaultdict

    pts: dict[tuple[int, int], list[float]] = {}

    # Axial coordinates → cartesian
    def axial_to_cart(q: int, r: int) -> list[float]:
        x = spacing * (q + 0.5 * r)
        y = spacing * (np.sqrt(3) / 2 * r)
        return [x, y, 0.0]

    # Generate hexagonal region of given ring count
    for q in range(-rings, rings + 1):
        for r in range(-rings, rings + 1):
            if abs(q + r) <= rings:
                pts[(q, r)] = axial_to_cart(q, r)

    pt_list = list(pts.keys())
    pt_idx = {k: i for i, k in enumerate(pt_list)}
    vertices = np.array([pts[k] for k in pt_list], dtype=float)

    # Hex neighbors: 6 axial directions
    directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
    edges: list[list[int]] = []
    seen: set[frozenset[int]] = set()
    for (q, r), i in pt_idx.items():
        for dq, dr in directions:
            nb = (q + dq, r + dr)
            if nb in pt_idx:
                j = pt_idx[nb]
                key = frozenset([i, j])
                if key not in seen:
                    seen.add(key)
                    edges.append([i, j])

    return MeshState(
        vertices=vertices,
        edges=np.array(edges, dtype=int),
        metadata={"type": "hex", "rings": rings, "spacing": spacing},
    )


def make_radial_mesh(
    n_rings: int = 5,
    n_sectors: int = 8,
    spacing: float = 1.0,
) -> MeshState:
    """Radial spoke-and-ring lattice (wheel-like topology)."""
    verts: list[list[float]] = [[0.0, 0.0, 0.0]]  # centre node
    edges: list[list[int]] = []

    ring_starts: list[int] = []
    for ring in range(1, n_rings + 1):
        r = ring * spacing
        ring_start = len(verts)
        ring_starts.append(ring_start)
        for s in range(n_sectors):
            angle = 2 * np.pi * s / n_sectors
            verts.append([r * np.cos(angle), r * np.sin(angle), 0.0])

        # Spoke edges (ring 1 connects to centre; others to previous ring)
        for s in range(n_sectors):
            cur = ring_start + s
            if ring == 1:
                edges.append([0, cur])
            else:
                prev = ring_starts[ring - 2] + s
                edges.append([prev, cur])

        # Ring circumferential edges
        for s in range(n_sectors):
            a = ring_start + s
            b = ring_start + (s + 1) % n_sectors
            edges.append([a, b])

    vertices = np.array(verts, dtype=float)
    return MeshState(
        vertices=vertices,
        edges=np.array(edges, dtype=int),
        metadata={"type": "radial", "n_rings": n_rings, "n_sectors": n_sectors},
    )

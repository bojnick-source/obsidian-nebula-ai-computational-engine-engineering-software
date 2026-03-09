"""Boundary condition definitions and node-set resolvers.

BoundaryCondition objects specify which DOFs are fixed (supports) and
which nodes carry applied loads. The resolver translates keyword node-set
names (e.g. "bottom_row") into concrete node indices at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..geometry.base_mesh import MeshState


@dataclass
class Support:
    """Fixed-DOF boundary condition on a set of nodes."""
    node_indices: list[int]
    dofs: list[int] = field(default_factory=lambda: [0, 1, 2])  # 0=X,1=Y,2=Z


@dataclass
class PointLoad:
    """Concentrated force applied to a set of nodes."""
    node_indices: list[int]
    force: np.ndarray   # shape (3,) in global frame, units: N

    def __post_init__(self) -> None:
        self.force = np.asarray(self.force, dtype=float)
        if self.force.shape != (3,):
            raise ValueError("force must be a 3-vector")


@dataclass
class BoundaryConditions:
    supports: list[Support] = field(default_factory=list)
    loads: list[PointLoad] = field(default_factory=list)

    def fixed_dofs(self, n_nodes: int) -> list[int]:
        """Return sorted list of globally fixed DOF indices."""
        fixed: set[int] = set()
        for s in self.supports:
            for ni in s.node_indices:
                for d in s.dofs:
                    fixed.add(3 * ni + d)
        return sorted(fixed)

    def force_vector(self, n_nodes: int) -> np.ndarray:
        """Assemble global force vector f of shape (3*n_nodes,)."""
        f = np.zeros(3 * n_nodes)
        for load in self.loads:
            for ni in load.node_indices:
                f[3 * ni: 3 * ni + 3] += load.force
        return f


# ── Node-set keyword resolver ─────────────────────────────────────────────────

def resolve_node_set(keyword: str, mesh: MeshState) -> list[int]:
    """Translate a keyword like 'bottom_row' into a list of node indices.

    Supports
    --------
    bottom_row      — nodes with minimum Y coordinate
    top_row         — nodes with maximum Y coordinate
    left_col        — nodes with minimum X coordinate
    right_col       — nodes with maximum X coordinate
    top_center      — single node closest to (cx, y_max, 0)
    bottom_center   — single node closest to (cx, y_min, 0)
    center          — single node closest to centroid
    all             — all nodes
    """
    v = mesh.vertices
    tol = 1e-6 * np.ptp(v, axis=0).max() if np.ptp(v, axis=0).max() > 0 else 1e-6

    if keyword == "bottom_row":
        y_min = np.min(v[:, 1])
        return [int(i) for i in np.where(np.abs(v[:, 1] - y_min) < tol)[0]]
    elif keyword == "top_row":
        y_max = np.max(v[:, 1])
        return [int(i) for i in np.where(np.abs(v[:, 1] - y_max) < tol)[0]]
    elif keyword == "left_col":
        x_min = np.min(v[:, 0])
        return [int(i) for i in np.where(np.abs(v[:, 0] - x_min) < tol)[0]]
    elif keyword == "right_col":
        x_max = np.max(v[:, 0])
        return [int(i) for i in np.where(np.abs(v[:, 0] - x_max) < tol)[0]]
    elif keyword == "top_center":
        y_max = np.max(v[:, 1])
        cx = np.mean(v[:, 0])
        top = np.where(np.abs(v[:, 1] - y_max) < tol)[0]
        if len(top) == 0:
            return []
        idx = top[np.argmin(np.abs(v[top, 0] - cx))]
        return [int(idx)]
    elif keyword == "bottom_center":
        y_min = np.min(v[:, 1])
        cx = np.mean(v[:, 0])
        bot = np.where(np.abs(v[:, 1] - y_min) < tol)[0]
        if len(bot) == 0:
            return []
        idx = bot[np.argmin(np.abs(v[bot, 0] - cx))]
        return [int(idx)]
    elif keyword == "center":
        centroid = np.mean(v, axis=0)
        idx = int(np.argmin(np.linalg.norm(v - centroid, axis=1)))
        return [idx]
    elif keyword == "all":
        return list(range(mesh.n_nodes))
    else:
        raise ValueError(f"Unknown node-set keyword: {keyword!r}")


def build_boundary_conditions(cfg: dict, mesh: MeshState) -> BoundaryConditions:
    """Build BoundaryConditions from the YAML config dict and a concrete mesh.

    Expected cfg structure (mirrors design_space.yaml):
        supports:
          - type: pin
            nodes: bottom_row
            dofs: [0, 1, 2]
        loads:
          - type: point
            nodes: top_center
            force: [0.0, -1000.0, 0.0]
    """
    bc = BoundaryConditions()

    for s_cfg in cfg.get("supports", []):
        node_kw = s_cfg["nodes"]
        node_ids = resolve_node_set(node_kw, mesh)
        dofs = list(s_cfg.get("dofs", [0, 1, 2]))
        bc.supports.append(Support(node_indices=node_ids, dofs=dofs))

    for l_cfg in cfg.get("loads", []):
        node_kw = l_cfg["nodes"]
        node_ids = resolve_node_set(node_kw, mesh)
        force = np.array(l_cfg["force"], dtype=float)
        bc.loads.append(PointLoad(node_indices=node_ids, force=force))

    return bc

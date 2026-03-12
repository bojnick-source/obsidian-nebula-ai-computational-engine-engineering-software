"""3D Direct-Stiffness Truss Solver.

Implements the classical direct-stiffness method for pin-jointed space trusses
using scipy.sparse CSR matrices for memory-efficient assembly.

Theory
------
For a member connecting nodes i and j:
    L = ||r_j - r_i||
    direction cosines: (l, m, n) = (r_j - r_i) / L
    axial stiffness:   k = A*E/L
    local stiffness:   K_loc = k * [[1,-1],[-1,1]]
    transformation:    T = [[l m n 0 0 0],[0 0 0 l m n]]
    global stiffness:  K_e = T.T @ K_loc @ T  (6x6)

Assembly:
    K[np.ix_(dofs_m, dofs_m)] += K_e

Boundary conditions: eliminate fixed DOFs by index deletion from K and f.

Solve: K_reduced @ u_free = f_reduced  using scipy.sparse.linalg.spsolve

Outputs
-------
    displacement    (3N,) full displacement vector (zeros at fixed DOFs)
    member_forces   (E,) axial member forces (tension+, compression-)
    member_stresses (E,) axial stresses σ = F/A
    compliance      f · u  (global stiffness measure; lower = stiffer)
    converged       bool
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from .structural_model import StructuralState


@dataclass
class SolverResult:
    converged: bool
    displacement: np.ndarray        # (3N,) — zeros at fixed DOFs
    member_forces: np.ndarray       # (E,) axial forces [N]
    member_stresses: np.ndarray     # (E,) axial stresses [Pa]
    compliance: float               # f · u — lower is stiffer
    max_displacement: float
    max_stress: float               # peak absolute stress
    residual: float                 # ||K u - f|| / ||f||
    reason: str = "ok"


def solve_truss(state: StructuralState) -> SolverResult:
    """Assemble and solve the global truss stiffness system.

    Parameters
    ----------
    state:
        Fully populated StructuralState (mesh + material + section + BC).

    Returns
    -------
    SolverResult
    """
    mesh = state.mesh
    n_nodes = mesh.n_nodes
    n_dof = 3 * n_nodes
    E = state.material.youngs_modulus
    areas = state.member_areas()

    v = mesh.vertices  # (N, 3)
    edges = mesh.edges  # (M, 2)

    # ── Assemble global stiffness matrix (CSR) ────────────────────────────────
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []

    for idx, (a, b) in enumerate(edges):
        diff = v[b] - v[a]
        L = float(np.linalg.norm(diff))
        if L < 1e-12:
            continue  # degenerate — skip (quality check should have caught this)

        cx, cy, cz = diff / L
        A = areas[idx]
        k = A * E / L

        # Direction cosine vector
        dc = np.array([cx, cy, cz])
        # 6x6 global stiffness contribution
        T = np.zeros((2, 6))
        T[0, :3] = dc
        T[1, 3:] = dc
        K_loc = k * np.array([[1.0, -1.0], [-1.0, 1.0]])
        K_e = T.T @ K_loc @ T  # (6, 6)

        dofs_a = [3 * a, 3 * a + 1, 3 * a + 2]
        dofs_b = [3 * b, 3 * b + 1, 3 * b + 2]
        dofs_m = dofs_a + dofs_b

        for ii in range(6):
            for jj in range(6):
                if abs(K_e[ii, jj]) > 1e-30:
                    rows.append(dofs_m[ii])
                    cols.append(dofs_m[jj])
                    data.append(K_e[ii, jj])

    K = sp.csr_matrix(
        (data, (rows, cols)),
        shape=(n_dof, n_dof),
        dtype=float,
    )

    # ── Assemble force vector ─────────────────────────────────────────────────
    f = state.bc.force_vector(n_nodes)

    # ── Apply boundary conditions (eliminate fixed DOFs) ─────────────────────
    fixed = state.bc.fixed_dofs(n_nodes)
    all_dofs = list(range(n_dof))
    free = sorted(set(all_dofs) - set(fixed))

    if not free:
        return _failed("all DOFs are fixed")

    K_red = K[np.ix_(free, free)]
    f_red = f[free]

    # Check the reduced system is non-singular
    if K_red.shape[0] == 0:
        return _failed("empty reduced system")

    # ── Solve ─────────────────────────────────────────────────────────────────
    try:
        u_free = spla.spsolve(K_red.tocsr(), f_red)
    except Exception as exc:
        return _failed(f"spsolve failed: {exc}")

    if not np.all(np.isfinite(u_free)):
        return _failed("non-finite displacements — singular stiffness matrix")

    # Reconstruct full displacement vector
    u = np.zeros(n_dof)
    u[free] = u_free

    # ── Compute member forces and stresses ────────────────────────────────────
    member_forces = np.zeros(len(edges))
    member_stresses = np.zeros(len(edges))

    for idx, (a, b) in enumerate(edges):
        diff = v[b] - v[a]
        L = float(np.linalg.norm(diff))
        if L < 1e-12:
            continue
        dc = diff / L
        A = areas[idx]
        k = A * E / L

        u_a = u[3 * a: 3 * a + 3]
        u_b = u[3 * b: 3 * b + 3]
        # Elongation projected along member axis
        delta = float(np.dot(u_b - u_a, dc))
        F = k * delta
        member_forces[idx] = F
        member_stresses[idx] = F / A

    # ── Compliance ────────────────────────────────────────────────────────────
    compliance = float(f @ u)  # = u^T K u = f^T u for elastic equilibrium

    # Residual (relative)
    residual_vec = K @ u - f
    f_norm = np.linalg.norm(f)
    residual = float(np.linalg.norm(residual_vec) / (f_norm + 1e-12))

    return SolverResult(
        converged=True,
        displacement=u,
        member_forces=member_forces,
        member_stresses=member_stresses,
        compliance=compliance,
        max_displacement=float(np.max(np.abs(u))),
        max_stress=float(np.max(np.abs(member_stresses))),
        residual=residual,
        reason="ok",
    )


def _failed(reason: str) -> SolverResult:
    empty = np.array([])
    return SolverResult(
        converged=False,
        displacement=empty,
        member_forces=empty,
        member_stresses=empty,
        compliance=float("inf"),
        max_displacement=float("inf"),
        max_stress=float("inf"),
        residual=float("inf"),
        reason=reason,
    )

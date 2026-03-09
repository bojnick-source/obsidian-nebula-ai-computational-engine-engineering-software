"""StructuralState: assembles material and section properties for a mesh.

This is the data preparation layer between geometry and the solver.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..geometry.base_mesh import MeshState
from .boundary_conditions import BoundaryConditions, build_boundary_conditions


@dataclass
class MaterialProperties:
    youngs_modulus: float   # Pa
    density: float          # kg/m³
    yield_stress: float     # Pa


@dataclass
class SectionProperties:
    """Per-member cross-sectional area (m²)."""
    area: float             # uniform baseline

    def member_area(self, member_idx: int) -> float:
        """Uniform section in Phase 1; override for variable-thickness."""
        return self.area


@dataclass
class StructuralState:
    """All data required by the solver for one evaluation."""
    mesh: MeshState
    material: MaterialProperties
    section: SectionProperties
    bc: BoundaryConditions

    @property
    def n_dof(self) -> int:
        return 3 * self.mesh.n_nodes

    def member_areas(self) -> np.ndarray:
        """(E,) array of cross-sectional areas."""
        return np.full(self.mesh.n_edges, self.section.area)

    def total_mass(self) -> float:
        """Approximate truss mass = Σ(A_i * L_i * ρ)."""
        v = self.mesh.vertices
        e = self.mesh.edges
        lengths = np.linalg.norm(v[e[:, 1]] - v[e[:, 0]], axis=1)
        areas = self.member_areas()
        return float(np.sum(areas * lengths * self.material.density))


def build_structural_state(
    mesh: MeshState,
    params: dict,
    cfg: dict,
) -> StructuralState:
    """Construct a StructuralState from a morphed mesh and full config dict.

    The 'thickness' parameter scales the base cross-sectional area.
    """
    mat_cfg = cfg.get("material", {})
    sec_cfg = cfg.get("section", {})
    bc_cfg = cfg.get("boundary_conditions", {})

    material = MaterialProperties(
        youngs_modulus=float(mat_cfg.get("youngs_modulus", 200e9)),
        density=float(mat_cfg.get("density", 7850.0)),
        yield_stress=float(mat_cfg.get("yield_stress", 250e6)),
    )

    area_base = float(sec_cfg.get("area_base", 1e-4))
    # Scale area by the thickness param (log-mapped, so always positive)
    thickness = float(params.get("thickness", 0.05))
    thickness_scale = thickness / 0.05   # normalised to mid-range
    effective_area = area_base * thickness_scale

    section = SectionProperties(area=max(effective_area, 1e-8))

    bc = build_boundary_conditions(bc_cfg, mesh)

    return StructuralState(mesh=mesh, material=material, section=section, bc=bc)

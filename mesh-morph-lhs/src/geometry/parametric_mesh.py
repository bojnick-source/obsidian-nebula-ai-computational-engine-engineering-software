"""ParametricMesh: wraps a base MeshState with a morph-and-validate pipeline.

Usage
-----
    pm = ParametricMesh.from_config(cfg["base_mesh"])
    morphed = pm.apply(params)
    quality = morphed.quality
    if quality["is_valid"] and quality["topology_valid"]:
        ...
"""

from __future__ import annotations

from dataclasses import dataclass

from .base_mesh import MeshState, make_grid_mesh, make_hex_mesh, make_radial_mesh
from .mesh_quality import compute_quality
from .morph_ops import morph_mesh
from .topology_rules import full_topology_check


@dataclass
class MorphedMesh:
    """Result of applying params to a ParametricMesh."""
    mesh: MeshState
    quality: dict
    topology: dict

    @property
    def is_simulation_ready(self) -> bool:
        return self.quality["is_valid"] and self.topology["topology_valid"]


class ParametricMesh:
    """Holds a base mesh and applies parameterised morphing on demand."""

    def __init__(self, base: MeshState) -> None:
        self._base = base

    @classmethod
    def from_config(cls, cfg: dict) -> "ParametricMesh":
        """Build from the ``base_mesh`` section of design_space.yaml."""
        mesh_type = cfg.get("type", "grid")
        spacing = float(cfg.get("spacing", 1.0))
        diagonals = bool(cfg.get("diagonals", True))

        if mesh_type == "grid":
            base = make_grid_mesh(
                nx=int(cfg.get("nx", 8)),
                ny=int(cfg.get("ny", 8)),
                nz=int(cfg.get("nz", 1)),
                spacing=spacing,
                diagonals=diagonals,
            )
        elif mesh_type == "hex":
            base = make_hex_mesh(
                rings=int(cfg.get("rings", 3)),
                spacing=spacing,
            )
        elif mesh_type == "radial":
            base = make_radial_mesh(
                n_rings=int(cfg.get("n_rings", 5)),
                n_sectors=int(cfg.get("n_sectors", 8)),
                spacing=spacing,
            )
        else:
            raise ValueError(f"Unknown base mesh type: {mesh_type!r}")

        return cls(base)

    @property
    def base(self) -> MeshState:
        return self._base

    def apply(self, params: dict) -> MorphedMesh:
        """Morph the base mesh with the given parameter dict and validate."""
        mesh = morph_mesh(self._base, params)
        quality = compute_quality(mesh)
        topology = full_topology_check(mesh)
        return MorphedMesh(mesh=mesh, quality=quality, topology=topology)

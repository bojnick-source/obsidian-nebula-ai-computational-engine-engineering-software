"""Component placement — Steps 1 & 2 of the assembly skill.

Defines the global coordinate system and places all components into it
using interface records as positioning constraints.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Coordinate system descriptor
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AssemblyCoordinateSystem:
    """Global frame definition for the assembly."""
    origin_description: str = "nose tip of fuselage"
    x_axis: str = "aft (positive toward tail)"
    y_axis: str = "starboard (positive to right)"
    z_axis: str = "up (positive toward sky)"
    units: str = "mm"
    # Reference planes (descriptive)
    plane_CL: str = "y=0 (centerline / plane of symmetry)"
    plane_FS1: str = "x=0 (fuselage station 0)"
    plane_WL0: str = "z=0 (waterline datum)"


# ─────────────────────────────────────────────────────────────────────────────
# Component placement
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ComponentPlacement:
    """Global position and orientation of one component."""
    component_id: str
    name: str
    translation_mm: tuple[float, float, float]   # (x, y, z) in global frame
    rotation_deg: tuple[float, float, float]      # (rx, ry, rz) Euler ZYX
    stl_path: str
    mass_kg: float
    is_symmetric: bool = False                    # true → mirror counterpart exists
    mirror_axis: str | None = None                # "y" = left-right symmetry
    # Computed after placement
    extraction_direction: tuple[float, float, float] = (0.0, 0.0, 1.0)  # default +Z

    def transform_matrix(self) -> np.ndarray:
        """4×4 homogeneous transform placing component in global frame."""
        rx, ry, rz = [np.radians(a) for a in self.rotation_deg]
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(rx), -np.sin(rx)],
            [0, np.sin(rx),  np.cos(rx)],
        ])
        Ry = np.array([
            [ np.cos(ry), 0, np.sin(ry)],
            [0, 1, 0],
            [-np.sin(ry), 0, np.cos(ry)],
        ])
        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0],
            [np.sin(rz),  np.cos(rz), 0],
            [0, 0, 1],
        ])
        R = Rz @ Ry @ Rx
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = self.translation_mm
        return T


# ─────────────────────────────────────────────────────────────────────────────
# Placement engine
# ─────────────────────────────────────────────────────────────────────────────

class ComponentPlacer:
    """Place all components into the global frame using interface constraints."""

    def __init__(self, primary_component_id: str = "C-001") -> None:
        self._primary_id = primary_component_id

    def place_all(
        self,
        components: list[dict[str, Any]],
        interfaces: list[dict[str, Any]],
    ) -> list[ComponentPlacement]:
        """Place every component. Raises RuntimeError if graph cannot be resolved."""
        placements: list[ComponentPlacement] = []
        placed_ids: set[str] = set()

        # Place primary component at origin
        primary = next(
            (c for c in components if c["id"] == self._primary_id), components[0]
        )
        placements.append(ComponentPlacement(
            component_id=primary["id"],
            name=primary.get("name", primary["id"]),
            translation_mm=(0.0, 0.0, 0.0),
            rotation_deg=(0.0, 0.0, 0.0),
            stl_path=primary.get("stl_path", ""),
            mass_kg=primary.get("mass_kg", 0.0),
        ))
        placed_ids.add(primary["id"])

        max_iterations = len(components) * 2
        iteration = 0

        while len(placed_ids) < len(components):
            iteration += 1
            if iteration > max_iterations:
                unplaced = [c["id"] for c in components if c["id"] not in placed_ids]
                raise RuntimeError(
                    f"Cannot place all components — unplaced: {unplaced}. "
                    f"Check that every component has an interface connecting it to "
                    f"at least one already-placed component."
                )

            placed_in_pass = False
            for comp in components:
                if comp["id"] in placed_ids:
                    continue

                # Find interface connecting this component to a placed neighbour
                anchoring_ifc = next(
                    (
                        ifc for ifc in interfaces
                        if comp["id"] in ifc.get("component_ids", [])
                        and any(cid in placed_ids for cid in ifc.get("component_ids", []))
                    ),
                    None,
                )
                if anchoring_ifc is None:
                    continue

                placement = self._from_interface(comp, anchoring_ifc, placements, placed_ids)
                placements.append(placement)
                placed_ids.add(comp["id"])
                placed_in_pass = True

            if not placed_in_pass:
                break  # no progress — topology error, caught on next iteration start

        return placements

    # ------------------------------------------------------------------

    @staticmethod
    def _from_interface(
        component: dict[str, Any],
        interface: dict[str, Any],
        placements: list[ComponentPlacement],
        placed_ids: set[str],
    ) -> ComponentPlacement:
        """Derive placement from interface offset relative to placed neighbour."""
        neighbour_id = next(
            cid for cid in interface.get("component_ids", [])
            if cid in placed_ids
        )
        neighbour = next(p for p in placements if p.component_id == neighbour_id)

        offset: tuple[float, float, float] = interface.get("offset_mm", (0.0, 0.0, 0.0))
        translation = tuple(
            n + o for n, o in zip(neighbour.translation_mm, offset)
        )

        return ComponentPlacement(
            component_id=component["id"],
            name=component.get("name", component["id"]),
            translation_mm=translation,  # type: ignore[arg-type]
            rotation_deg=interface.get("rotation_deg", (0.0, 0.0, 0.0)),
            stl_path=component.get("stl_path", ""),
            mass_kg=component.get("mass_kg", 0.0),
            is_symmetric=interface.get("is_symmetric", False),
            mirror_axis=interface.get("mirror_axis"),
        )

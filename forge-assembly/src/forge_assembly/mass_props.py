"""Center of mass and mass budget — Step 4 of the assembly skill."""

from __future__ import annotations

from dataclasses import dataclass

from forge_assembly.placement import ComponentPlacement


@dataclass
class MassProperties:
    total_mass_kg: float
    center_of_mass_mm: tuple[float, float, float]
    mass_by_component: dict[str, float]
    mass_budget_kg: float | None = None
    # Populated when budget is known
    mass_margin_kg: float | None = None
    over_budget: bool = False


def compute_mass_properties(
    placements: list[ComponentPlacement],
    mass_budget_kg: float | None = None,
) -> MassProperties:
    """Compute total mass and CG from component placements.

    CG is computed from component centroid positions (not mesh centroids).
    This is a fast approximation; mesh-level CG requires trimesh.
    """
    total = sum(p.mass_kg for p in placements)
    if total == 0.0:
        return MassProperties(
            total_mass_kg=0.0,
            center_of_mass_mm=(0.0, 0.0, 0.0),
            mass_by_component={p.component_id: p.mass_kg for p in placements},
            mass_budget_kg=mass_budget_kg,
        )

    cx = sum(p.mass_kg * p.translation_mm[0] for p in placements) / total
    cy = sum(p.mass_kg * p.translation_mm[1] for p in placements) / total
    cz = sum(p.mass_kg * p.translation_mm[2] for p in placements) / total

    margin = (mass_budget_kg - total) if mass_budget_kg is not None else None
    over = margin is not None and margin < 0.0

    return MassProperties(
        total_mass_kg=total,
        center_of_mass_mm=(cx, cy, cz),
        mass_by_component={p.component_id: p.mass_kg for p in placements},
        mass_budget_kg=mass_budget_kg,
        mass_margin_kg=margin,
        over_budget=over,
    )

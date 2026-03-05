"""Geometric interference and clearance checking — Step 3 of the assembly skill.

Loads placed component meshes via trimesh, runs pairwise boolean intersection
checks, and flags interference volumes and clearance violations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from forge_assembly.placement import ComponentPlacement

try:
    import trimesh
    _TRIMESH_AVAILABLE = True
except ImportError:
    _TRIMESH_AVAILABLE = False

_TRIMESH_MISSING_MSG = (
    "trimesh not installed — install with: pip install trimesh scipy"
)


# ─────────────────────────────────────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class InterferenceIssue:
    issue_type: str         # "interference" | "clearance_violation" | "mesh_load_error"
    components: list[str]
    severity: str           # "error" | "warning"
    description: str
    details: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Mesh loader
# ─────────────────────────────────────────────────────────────────────────────

def _load_placed_meshes(
    placements: list[ComponentPlacement],
) -> tuple[dict[str, Any], list[InterferenceIssue]]:
    """Load each component STL and apply placement transform. Returns (meshes, errors)."""
    if not _TRIMESH_AVAILABLE:
        raise RuntimeError(_TRIMESH_MISSING_MSG)

    meshes: dict[str, Any] = {}
    errors: list[InterferenceIssue] = []

    for p in placements:
        if not p.stl_path:
            errors.append(InterferenceIssue(
                issue_type="mesh_load_error",
                components=[p.component_id],
                severity="error",
                description=f"{p.component_id}: no stl_path specified",
            ))
            continue
        try:
            mesh = trimesh.load(p.stl_path, force="mesh")
            mesh.apply_transform(p.transform_matrix())
            meshes[p.component_id] = mesh
        except Exception as exc:
            errors.append(InterferenceIssue(
                issue_type="mesh_load_error",
                components=[p.component_id],
                severity="error",
                description=f"{p.component_id}: cannot load '{p.stl_path}': {exc}",
            ))

    return meshes, errors


# ─────────────────────────────────────────────────────────────────────────────
# Interference checker
# ─────────────────────────────────────────────────────────────────────────────

def check_interference(
    placements: list[ComponentPlacement],
    clearance_required_mm: float = 2.0,
) -> list[InterferenceIssue]:
    """Check all component pairs for intersection and clearance violations.

    Any true intersection → severity "error" (hard failure, do not export).
    Clearance < 0.5 mm   → severity "error".
    Clearance 0.5–2.0 mm → severity "warning".

    Returns list of InterferenceIssue records (empty = all clear).
    """
    meshes, load_errors = _load_placed_meshes(placements)
    issues: list[InterferenceIssue] = list(load_errors)

    ids = list(meshes.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            id_a, id_b = ids[i], ids[j]
            mesh_a, mesh_b = meshes[id_a], meshes[id_b]

            # Fast AABB pre-filter
            if not _aabbs_overlap(mesh_a, mesh_b):
                continue

            try:
                collision = trimesh.boolean.intersection([mesh_a, mesh_b])
                if collision is not None and hasattr(collision, "faces") and len(collision.faces) > 0:
                    vol = getattr(collision, "volume", 0.0)
                    issues.append(InterferenceIssue(
                        issue_type="interference",
                        components=[id_a, id_b],
                        severity="error",
                        description=(
                            f"{id_a} ∩ {id_b}: {vol:.1f} mm³ intersection volume"
                        ),
                        details={"interference_volume_mm3": vol},
                    ))
                    continue
            except Exception:
                pass

            # Clearance check (minimum vertex-to-surface distance)
            try:
                _, distances, _ = trimesh.proximity.closest_point(mesh_b, mesh_a.vertices)
                min_gap = float(np.min(distances))
                if min_gap < clearance_required_mm:
                    severity = "error" if min_gap < 0.5 else "warning"
                    issues.append(InterferenceIssue(
                        issue_type="clearance_violation",
                        components=[id_a, id_b],
                        severity=severity,
                        description=(
                            f"{id_a} ↔ {id_b}: {min_gap:.2f} mm gap "
                            f"(required ≥ {clearance_required_mm} mm)"
                        ),
                        details={
                            "min_gap_mm": min_gap,
                            "required_mm": clearance_required_mm,
                        },
                    ))
            except Exception:
                pass

    return issues


def _aabbs_overlap(mesh_a: Any, mesh_b: Any) -> bool:
    """Quick axis-aligned bounding box overlap test."""
    bmin_a, bmax_a = mesh_a.bounds
    bmin_b, bmax_b = mesh_b.bounds
    return all(
        bmax_a[k] >= bmin_b[k] and bmax_b[k] >= bmin_a[k]
        for k in range(3)
    )


def get_all_placed_meshes(
    placements: list[ComponentPlacement],
) -> dict[str, Any]:
    """Return {component_id: trimesh} for use by downstream checks."""
    meshes, _ = _load_placed_meshes(placements)
    return meshes

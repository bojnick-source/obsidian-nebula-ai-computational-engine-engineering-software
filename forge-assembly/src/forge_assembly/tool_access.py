"""DFA tool access volume check — Step 6 of the assembly skill.

For every fastener, generates the tool's swept solid volume, then
boolean-intersects it with the assembled geometry to determine whether
the tool can physically reach and operate the fastener.

Also performs a line-of-sight visual access check.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from forge_assembly.fasteners import (
    FASTENER_TOOL_MAP,
    TOOL_DATABASE,
    FastenerSpec,
    ToolGeometry,
)

try:
    import trimesh
    _TRIMESH_AVAILABLE = True
except ImportError:
    _TRIMESH_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ToolAccessResult:
    interface_id: str
    fastener_type: str
    position_mm: tuple[float, float, float]
    issue_type: str      # "clear" | "tool_access_blocked" | "visual_access_blocked" | "unknown_fastener_tool"
    severity: str        # "ok" | "warning" | "error"
    description: str
    tools_checked: list[dict[str, Any]] = field(default_factory=list)
    blind_assembly_required: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Tool volume generator
# ─────────────────────────────────────────────────────────────────────────────

def _generate_tool_volume(
    position_mm: tuple[float, float, float],
    fastener_axis: tuple[float, float, float],
    tool: ToolGeometry,
) -> Any:
    """Generate the swept solid volume a tool occupies at a given fastener location.

    Returns a trimesh.Trimesh solid in global coordinates.
    Raises RuntimeError if trimesh unavailable.
    """
    if not _TRIMESH_AVAILABLE:
        raise RuntimeError("trimesh required for tool access check")

    volumes = []

    # 1. Approach cylinder (tool head + clearance along fastener axis)
    approach = trimesh.creation.cylinder(
        radius=tool.approach_diameter_mm / 2,
        height=tool.approach_length_mm,
        sections=32,
    )
    approach.apply_translation([0, 0, tool.approach_length_mm / 2])
    volumes.append(approach)

    # 2. Swing annulus (handle arc) — approximated as solid cylinder at approach depth
    if tool.swing_radius_mm > 0 and tool.swing_arc_deg > 0:
        swing = trimesh.creation.cylinder(
            radius=tool.swing_radius_mm,
            height=40.0,  # ~handle cross-section
            sections=32,
        )
        swing.apply_translation([0, 0, tool.approach_length_mm + 20.0])
        volumes.append(swing)

    # 3. Hand clearance envelope (for hand-held tools)
    if tool.hand_clearance_diameter_mm > 0:
        hand = trimesh.creation.cylinder(
            radius=tool.hand_clearance_diameter_mm / 2,
            height=tool.hand_clearance_length_mm,
            sections=32,
        )
        hand.apply_translation([
            0, 0,
            tool.approach_length_mm + tool.hand_clearance_length_mm / 2,
        ])
        volumes.append(hand)

    # Union volumes
    tool_vol = volumes[0]
    for v in volumes[1:]:
        try:
            tool_vol = trimesh.boolean.union([tool_vol, v])
        except Exception:
            combined = trimesh.util.concatenate([tool_vol, v])
            tool_vol = combined.convex_hull

    # Orient to fastener axis (default cylinder Z → fastener_axis)
    axis = np.array(fastener_axis, dtype=float)
    axis /= np.linalg.norm(axis)
    z = np.array([0.0, 0.0, 1.0])

    if not np.allclose(axis, z):
        rot_axis = np.cross(z, axis)
        norm = np.linalg.norm(rot_axis)
        if norm > 1e-10:
            rot_axis /= norm
            angle = np.arccos(np.clip(np.dot(z, axis), -1.0, 1.0))
            R = trimesh.transformations.rotation_matrix(angle, rot_axis)
            tool_vol.apply_transform(R)

    tool_vol.apply_translation(position_mm)
    return tool_vol


# ─────────────────────────────────────────────────────────────────────────────
# Main checker
# ─────────────────────────────────────────────────────────────────────────────

def check_tool_access(
    assembled_meshes: dict[str, Any],
    fastener_specs: list[FastenerSpec],
) -> list[ToolAccessResult]:
    """Check every fastener for physical tool access in the assembled state.

    assembled_meshes: {component_id: trimesh in global coords}
    Returns list of ToolAccessResult (one per fastener).
    """
    if not _TRIMESH_AVAILABLE:
        raise RuntimeError("trimesh required: pip install trimesh scipy")

    results: list[ToolAccessResult] = []

    # Union all assembly geometry for collision checks
    all_meshes = list(assembled_meshes.values())
    assembly = all_meshes[0]
    for m in all_meshes[1:]:
        try:
            assembly = trimesh.boolean.union([assembly, m])
        except Exception:
            assembly = trimesh.util.concatenate([assembly, m])

    for spec in fastener_specs:
        tool_keys = FASTENER_TOOL_MAP.get(spec.fastener_type, [])

        if not tool_keys:
            results.append(ToolAccessResult(
                interface_id=spec.interface_id,
                fastener_type=spec.fastener_type,
                position_mm=spec.position_mm,
                issue_type="unknown_fastener_tool",
                severity="warning",
                description=(
                    f"{spec.interface_id}: no tool mapping for '{spec.fastener_type}'"
                ),
            ))
            continue

        any_clear = False
        tools_checked: list[dict[str, Any]] = []

        for tool_key in tool_keys:
            tool = TOOL_DATABASE.get(tool_key)
            if tool is None:
                continue

            try:
                vol = _generate_tool_volume(spec.position_mm, spec.axis, tool)
                collision = trimesh.boolean.intersection([vol, assembly])
                blocked = (
                    collision is not None
                    and hasattr(collision, "faces")
                    and len(collision.faces) > 0
                    and getattr(collision, "volume", 0.0) > 1.0  # >1 mm³ = real hit
                )
            except Exception:
                # Boolean failed — bounding box fallback
                try:
                    vol = _generate_tool_volume(spec.position_mm, spec.axis, tool)
                    _, dists, _ = trimesh.proximity.closest_point(assembly, vol.vertices)
                    blocked = float(np.min(dists)) < 0.5
                except Exception:
                    blocked = False  # cannot determine — assume clear

            tool_status = "BLOCKED" if blocked else "CLEAR"
            if not blocked:
                any_clear = True
            tools_checked.append({"tool": tool.name, "status": tool_status})
            if not blocked:
                break  # one clear tool is sufficient

        if any_clear:
            results.append(ToolAccessResult(
                interface_id=spec.interface_id,
                fastener_type=spec.fastener_type,
                position_mm=spec.position_mm,
                issue_type="clear",
                severity="ok",
                description=f"{spec.interface_id}: tool access clear",
                tools_checked=tools_checked,
            ))
        else:
            blocked_names = [t["tool"] for t in tools_checked if t["status"] == "BLOCKED"]
            results.append(ToolAccessResult(
                interface_id=spec.interface_id,
                fastener_type=spec.fastener_type,
                position_mm=spec.position_mm,
                issue_type="tool_access_blocked",
                severity="error",
                description=(
                    f"[TOOL ACCESS BLOCKED] {spec.interface_id}: "
                    f"no tool can reach {spec.fastener_type} at {spec.position_mm}. "
                    f"Blocked tools: {', '.join(blocked_names)}"
                ),
                tools_checked=tools_checked,
            ))

        # Visual line-of-sight check (30° cone)
        results.append(_check_visual_access(assembly, spec))

    return [r for r in results if r.severity != "ok" or r.issue_type == "clear"]


def _check_visual_access(
    assembly: Any,
    spec: FastenerSpec,
) -> ToolAccessResult:
    """Ray-cast in 30° cone around fastener axis. All blocked → blind assembly."""
    pos = np.array(spec.position_mm, dtype=float)
    axis = np.array(spec.axis, dtype=float)
    axis /= np.linalg.norm(axis)

    perp = np.array([1, 0, 0]) if abs(axis[0]) < 0.9 else np.array([0, 1, 0])
    perp = np.cross(axis, perp)
    perp /= np.linalg.norm(perp)

    n_rays = 12
    all_blocked = True
    for k in range(n_rays):
        angle = 2 * math.pi * k / n_rays
        ray_dir = (
            axis * math.cos(math.radians(30))
            + perp * math.sin(math.radians(30)) * math.cos(angle)
            + np.cross(axis, perp) * math.sin(math.radians(30)) * math.sin(angle)
        )
        try:
            locs = assembly.ray.intersects_location(
                ray_origins=[pos + axis * 5],
                ray_directions=[ray_dir],
            )
            if len(locs[0]) == 0:
                all_blocked = False
                break
        except Exception:
            all_blocked = False
            break

    if all_blocked:
        return ToolAccessResult(
            interface_id=spec.interface_id,
            fastener_type=spec.fastener_type,
            position_mm=spec.position_mm,
            issue_type="visual_access_blocked",
            severity="warning",
            description=(
                f"[VISUAL ACCESS BLOCKED] {spec.interface_id}: "
                f"fastener at {spec.position_mm} has no line-of-sight within 30° cone. "
                f"Blind assembly required."
            ),
            blind_assembly_required=True,
        )

    return ToolAccessResult(
        interface_id=spec.interface_id,
        fastener_type=spec.fastener_type,
        position_mm=spec.position_mm,
        issue_type="clear",
        severity="ok",
        description=f"{spec.interface_id}: visual access clear",
    )

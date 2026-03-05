"""Disassembly sequence generator — Step 7 of the assembly skill.

Builds a dependency DAG: component A blocks removal of B if A's geometry
is in B's extraction path. Topological sort (Kahn's algorithm) produces
a valid disassembly order.

Raises RuntimeError if a disassembly cycle is detected — that is a hard
design error requiring at least one joint redesign.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from forge_assembly.fasteners import FASTENER_TOOL_MAP
from forge_assembly.placement import ComponentPlacement
from forge_assembly.tool_access import ToolAccessResult


# Estimated removal time per fastener by joint type (trained technician)
_TIME_PER_FASTENER_MIN: dict[str, float] = {
    "bolted":    0.5,
    "snap_fit":  0.25,
    "press_fit": 2.0,
    "adhesive":  5.0,
    "riveted":   1.5,
    "welded":    0.0,   # non-removable → L3-factory, time irrelevant here
}

_DESTRUCTIVE_JOINTS = {"adhesive", "welded", "riveted"}


@dataclass
class DisassemblyNode:
    component_id: str
    name: str
    fastener_interfaces: list[str] = field(default_factory=list)
    blocks_removal_of: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    removal_tools: list[str] = field(default_factory=list)
    estimated_removal_time_min: float = 0.0
    joint_type: str = "bolted"
    non_destructive: bool = True
    service_level: str = "L1-field"  # filled in by maintenance classifier


@dataclass
class DisassemblyResult:
    nodes: list[DisassemblyNode]
    removal_order: list[str]          # component_ids, first = remove first
    total_estimated_time_min: float
    non_destructive_count: int
    total_count: int


def build_disassembly_dag(
    placements: list[ComponentPlacement],
    interfaces: list[dict[str, Any]],
    tool_access_results: list[ToolAccessResult],
) -> DisassemblyResult:
    """Build the disassembly DAG and return topologically sorted removal order.

    Raises RuntimeError if a disassembly cycle is detected.
    """
    node_map: dict[str, DisassemblyNode] = {}

    # Initialise all components
    for p in placements:
        iface_ids = [
            ifc.get("id", "")
            for ifc in interfaces
            if p.component_id in ifc.get("component_ids", [])
        ]
        node_map[p.component_id] = DisassemblyNode(
            component_id=p.component_id,
            name=p.name,
            fastener_interfaces=iface_ids,
        )

    # Populate joint type and tool info from interfaces
    for ifc in interfaces:
        joint = ifc.get("joint_type", "bolted")
        ftype = ifc.get("fastener_type", "")
        tools = FASTENER_TOOL_MAP.get(ftype, [])
        for cid in ifc.get("component_ids", []):
            if cid in node_map:
                node = node_map[cid]
                node.joint_type = joint
                node.non_destructive = joint not in _DESTRUCTIVE_JOINTS
                for t in tools:
                    if t not in node.removal_tools:
                        node.removal_tools.append(t)

    # Estimate removal times
    for node in node_map.values():
        n_fasteners = len(node.fastener_interfaces) * 4  # ~4 per interface
        time_each = _TIME_PER_FASTENER_MIN.get(node.joint_type, 1.0)
        node.estimated_removal_time_min = n_fasteners * time_each

    # Spatial blocking: component A blocks B if A is along B's extraction path
    _resolve_spatial_blocking(placements, node_map)

    # Kahn's topological sort
    in_degree: dict[str, int] = {cid: len(n.blocked_by) for cid, n in node_map.items()}
    queue = sorted(
        [cid for cid, deg in in_degree.items() if deg == 0],
        key=lambda c: node_map[c].estimated_removal_time_min,
    )
    removal_order: list[str] = []

    while queue:
        current = queue.pop(0)
        removal_order.append(current)
        for blocked_id in node_map[current].blocks_removal_of:
            in_degree[blocked_id] -= 1
            if in_degree[blocked_id] == 0:
                queue.append(blocked_id)
                queue.sort(key=lambda c: node_map[c].estimated_removal_time_min)

    if len(removal_order) < len(node_map):
        cycle = [cid for cid in node_map if cid not in removal_order]
        raise RuntimeError(
            f"[DISASSEMBLY CYCLE DETECTED] Components {cycle} form a mutual blocking "
            f"cycle. At least one joint must be redesigned for sequential access. "
            f"This is a hard design error."
        )

    nodes = list(node_map.values())
    total_time = sum(n.estimated_removal_time_min for n in nodes)
    nd_count = sum(1 for n in nodes if n.non_destructive)

    return DisassemblyResult(
        nodes=nodes,
        removal_order=removal_order,
        total_estimated_time_min=total_time,
        non_destructive_count=nd_count,
        total_count=len(nodes),
    )


def _resolve_spatial_blocking(
    placements: list[ComponentPlacement],
    node_map: dict[str, DisassemblyNode],
) -> None:
    """Heuristic: if component A is within 100 mm laterally and above B in
    extraction direction, A blocks removal of B."""
    extraction_dir = np.array([0.0, 0.0, 1.0])  # default +Z

    for p_b in placements:
        for p_a in placements:
            if p_a.component_id == p_b.component_id:
                continue
            delta = np.array(p_a.translation_mm) - np.array(p_b.translation_mm)
            projection = float(np.dot(delta, extraction_dir))
            lateral = float(np.linalg.norm(delta - projection * extraction_dir))

            # A is "above" B in extraction direction and within 100 mm laterally
            if projection > 0 and lateral < 100.0:
                a_id = p_a.component_id
                b_id = p_b.component_id
                if b_id not in node_map[a_id].blocks_removal_of:
                    node_map[a_id].blocks_removal_of.append(b_id)
                if a_id not in node_map[b_id].blocked_by:
                    node_map[b_id].blocked_by.append(a_id)


def format_disassembly_table(result: DisassemblyResult) -> str:
    """Return a human-readable disassembly sequence table."""
    node_map = {n.component_id: n for n in result.nodes}
    lines = [
        "=== DISASSEMBLY SEQUENCE ===",
        "",
        f"{'Order':<6} {'Component':<20} {'Blocked By':<22} {'Joint':<10} {'NDT':<5} {'Est.':<9} {'Tools'}",
        "─" * 90,
    ]
    for idx, cid in enumerate(result.removal_order, start=1):
        node = node_map[cid]
        prereqs = ", ".join(node.blocked_by) or "(none)"
        ndt = "✅" if node.non_destructive else "❌"
        tools_str = ", ".join(node.removal_tools[:2]) or "—"
        lines.append(
            f"{idx:<6} {node.name[:20]:<20} {prereqs[:22]:<22} "
            f"{node.joint_type:<10} {ndt:<5} "
            f"{node.estimated_removal_time_min:.1f} min  {tools_str}"
        )
    lines += [
        "─" * 90,
        f"Total estimated time: {result.total_estimated_time_min:.1f} min (trained technician)",
        f"Non-destructive: {result.non_destructive_count}/{result.total_count} components",
    ]
    return "\n".join(lines)

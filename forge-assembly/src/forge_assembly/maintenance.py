"""Maintenance access classification — Step 8 of the assembly skill.

Tags each component with a serviceability level following ATA iSpec 2200
principles:
  L1-field:   Hand tools, ≤30 min total, no prerequisites
  L2-depot:   ≤3 prerequisites, non-destructive, ≤4 hours total
  L3-factory: Everything else
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from forge_assembly.disassembly import DisassemblyResult


class ServiceLevel(StrEnum):
    L1_FIELD   = "L1-field"
    L2_DEPOT   = "L2-depot"
    L3_FACTORY = "L3-factory"


@dataclass
class MaintenanceClassification:
    component_id: str
    name: str
    level: ServiceLevel
    reason: str
    tools_required: list[str]
    estimated_time_min: float
    prerequisites: list[str]
    non_destructive: bool
    joint_type: str


@dataclass
class MaintenanceSummary:
    classifications: list[MaintenanceClassification]
    l1_count: int
    l2_count: int
    l3_count: int
    total_mass_kg: float
    field_replaceable_mass_kg: float
    field_replaceable_fraction: float
    serviceability_warnings: list[str]


# Components that MUST be L1-field or L2-depot (never L3)
_MUST_BE_FIELD_SERVICEABLE_KEYWORDS = {
    "motor", "battery", "esc", "propeller", "avionics",
    "flight controller", "servo", "gps", "receiver",
}


def classify_maintenance_access(
    disassembly_result: DisassemblyResult,
    component_masses: dict[str, float] | None = None,
    frequently_replaced: list[str] | None = None,
) -> MaintenanceSummary:
    """Classify every component's serviceability level.

    component_masses: {component_id: mass_kg} for field-replaceable fraction
    frequently_replaced: component_ids that must be L1/L2
    """
    node_map = {n.component_id: n for n in disassembly_result.nodes}
    masses = component_masses or {}
    must_be_serviceable = set(frequently_replaced or [])

    classifications: list[MaintenanceClassification] = []
    warnings: list[str] = []

    for node in disassembly_result.nodes:
        n_prereqs = len(node.blocked_by)

        # Total time including all prerequisites
        total_time = node.estimated_removal_time_min
        for prereq_id in node.blocked_by:
            if prereq_id in node_map:
                total_time += node_map[prereq_id].estimated_removal_time_min

        # Classify
        if (
            n_prereqs == 0
            and node.non_destructive
            and node.joint_type in ("bolted", "snap_fit")
            and total_time <= 30.0
        ):
            level = ServiceLevel.L1_FIELD
            reason = "Direct access, non-destructive, hand tools only"

        elif (
            n_prereqs <= 3
            and node.non_destructive
            and total_time <= 240.0
        ):
            level = ServiceLevel.L2_DEPOT
            reason = f"Requires removal of {n_prereqs} component(s) first"

        else:
            reasons = []
            if n_prereqs > 3:
                reasons.append(f"{n_prereqs} prerequisites")
            if not node.non_destructive:
                reasons.append(f"destructive joint ({node.joint_type})")
            if total_time > 240.0:
                reasons.append(f"est. {total_time:.0f} min total")
            level = ServiceLevel.L3_FACTORY
            reason = "Factory service required: " + ", ".join(reasons)

        # Check frequently-replaced components that ended up L3
        name_lower = node.name.lower()
        is_critical = (
            node.component_id in must_be_serviceable
            or any(kw in name_lower for kw in _MUST_BE_FIELD_SERVICEABLE_KEYWORDS)
        )
        if is_critical and level == ServiceLevel.L3_FACTORY:
            warnings.append(
                f"[SERVICEABILITY DESIGN ERROR] {node.name} ({node.component_id}) "
                f"is classified L3-factory but must be field-serviceable. "
                f"Redesign joint to enable field replacement."
            )

        classifications.append(MaintenanceClassification(
            component_id=node.component_id,
            name=node.name,
            level=level,
            reason=reason,
            tools_required=node.removal_tools,
            estimated_time_min=total_time,
            prerequisites=node.blocked_by,
            non_destructive=node.non_destructive,
            joint_type=node.joint_type,
        ))

    # Field-replaceable mass fraction
    total_mass = sum(masses.values()) if masses else 0.0
    field_mass = sum(
        masses.get(c.component_id, 0.0)
        for c in classifications
        if c.level in (ServiceLevel.L1_FIELD, ServiceLevel.L2_DEPOT)
    )
    fraction = field_mass / total_mass if total_mass > 0 else 0.0

    if total_mass > 0 and fraction < 0.30:
        warnings.append(
            f"[LOW SERVICEABILITY] Only {fraction:.0%} of assembly mass is "
            f"field-replaceable (target ≥ 30%). Review joint selections."
        )

    return MaintenanceSummary(
        classifications=classifications,
        l1_count=sum(1 for c in classifications if c.level == ServiceLevel.L1_FIELD),
        l2_count=sum(1 for c in classifications if c.level == ServiceLevel.L2_DEPOT),
        l3_count=sum(1 for c in classifications if c.level == ServiceLevel.L3_FACTORY),
        total_mass_kg=total_mass,
        field_replaceable_mass_kg=field_mass,
        field_replaceable_fraction=fraction,
        serviceability_warnings=warnings,
    )


def format_maintenance_table(summary: MaintenanceSummary) -> str:
    """Return human-readable maintenance classification table."""
    lines = [
        "=== MAINTENANCE ACCESS CLASSIFICATION ===",
        "",
        (
            f"L1-field: {summary.l1_count}  "
            f"L2-depot: {summary.l2_count}  "
            f"L3-factory: {summary.l3_count}  "
            f"Field-replaceable: {summary.field_replaceable_fraction:.0%}"
        ),
        "",
        f"{'Component':<22} {'Level':<12} {'NDT':<5} {'Prereqs':<8} {'Est. Time':<12} {'Reason'}",
        "─" * 95,
    ]
    for c in sorted(summary.classifications, key=lambda x: x.level.value):
        ndt = "✅" if c.non_destructive else "❌"
        lines.append(
            f"{c.name[:22]:<22} {c.level:<12} {ndt:<5} "
            f"{len(c.prerequisites):<8} {c.estimated_time_min:.1f} min     {c.reason[:40]}"
        )
    if summary.serviceability_warnings:
        lines += ["", "WARNINGS:"]
        for w in summary.serviceability_warnings:
            lines.append(f"  ⚠  {w}")
    return "\n".join(lines)

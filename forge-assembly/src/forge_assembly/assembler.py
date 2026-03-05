"""Top-level assembly orchestrator — runs all 9 steps in sequence.

Usage:
    assembler = AssemblyOrchestrator(vault_root=Path("/vault"), project="Aladdin-3B")
    result = assembler.run(components, interfaces, fastener_specs, mass_budget_kg=6.1)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from forge_assembly.disassembly import (
    DisassemblyResult,
    build_disassembly_dag,
    format_disassembly_table,
)
from forge_assembly.fasteners import FastenerSpec
from forge_assembly.interference import InterferenceIssue, check_interference
from forge_assembly.maintenance import (
    MaintenanceSummary,
    classify_maintenance_access,
    format_maintenance_table,
)
from forge_assembly.mass_props import MassProperties, compute_mass_properties
from forge_assembly.placement import AssemblyCoordinateSystem, ComponentPlacement, ComponentPlacer
from forge_assembly.tool_access import ToolAccessResult, check_tool_access
from forge_assembly.vault_writer import AssemblyVaultWriter

try:
    from forge_assembly.interference import get_all_placed_meshes
    _MESHES_AVAILABLE = True
except ImportError:
    _MESHES_AVAILABLE = False


@dataclass
class AssemblyReport:
    """Complete assembly analysis output."""
    run_id: str
    trace_id: str
    project: str
    coordinate_system: AssemblyCoordinateSystem
    placements: list[ComponentPlacement]
    mass_props: MassProperties
    interference_issues: list[InterferenceIssue]
    tool_access_results: list[ToolAccessResult]
    disassembly_result: DisassemblyResult
    maintenance_summary: MaintenanceSummary
    vault_paths: list[Path] = field(default_factory=list)
    # Overall pass/fail
    has_errors: bool = False
    error_summary: list[str] = field(default_factory=list)


class AssemblyOrchestrator:
    """Run the full 9-step assembly skill pipeline."""

    def __init__(
        self,
        vault_root: Path | None = None,
        project: str = "unknown",
        primary_component_id: str = "C-001",
        clearance_required_mm: float = 2.0,
        mass_budget_kg: float | None = None,
        run_tool_access: bool = True,  # disable if no STL files present
    ) -> None:
        self._vault_root = vault_root
        self._project = project
        self._clearance_mm = clearance_required_mm
        self._mass_budget = mass_budget_kg
        self._run_tool_access = run_tool_access
        self._placer = ComponentPlacer(primary_component_id)

    def run(
        self,
        components: list[dict[str, Any]],
        interfaces: list[dict[str, Any]],
        fastener_specs: list[FastenerSpec] | None = None,
        frequently_replaced: list[str] | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> AssemblyReport:
        """Execute all assembly steps and return a complete AssemblyReport."""
        _trace_id = trace_id or str(uuid.uuid4())
        _run_id = run_id or str(uuid.uuid4())
        coord_sys = AssemblyCoordinateSystem()

        # Step 1+2: Place components
        placements = self._placer.place_all(components, interfaces)

        # Step 3: Interference
        interference_issues: list[InterferenceIssue] = []
        if any(p.stl_path for p in placements):
            try:
                interference_issues = check_interference(placements, self._clearance_mm)
            except Exception as exc:
                interference_issues.append(InterferenceIssue(
                    issue_type="check_error",
                    components=[],
                    severity="warning",
                    description=f"Interference check failed: {exc}",
                ))

        # Step 4: Mass properties
        mass_props = compute_mass_properties(
            placements,
            mass_budget_kg=self._mass_budget,
        )

        # Steps 5+6: Tool access
        tool_access_results: list[ToolAccessResult] = []
        if self._run_tool_access and fastener_specs and any(p.stl_path for p in placements):
            try:
                meshes = get_all_placed_meshes(placements) if _MESHES_AVAILABLE else {}
                if meshes:
                    tool_access_results = check_tool_access(meshes, fastener_specs)
            except Exception as exc:
                tool_access_results.append(ToolAccessResult(
                    interface_id="—",
                    fastener_type="—",
                    position_mm=(0, 0, 0),
                    issue_type="check_error",
                    severity="warning",
                    description=f"Tool access check failed: {exc}",
                ))

        # Step 7: Disassembly DAG
        disassembly_result = build_disassembly_dag(
            placements, interfaces, tool_access_results
        )

        # Step 8: Maintenance classification
        comp_masses = {p.component_id: p.mass_kg for p in placements}
        maintenance_summary = classify_maintenance_access(
            disassembly_result,
            component_masses=comp_masses,
            frequently_replaced=frequently_replaced,
        )

        # Step 9: Vault write (if vault configured)
        vault_paths: list[Path] = []
        if self._vault_root is not None:
            try:
                writer = AssemblyVaultWriter(self._vault_root, self._project)
                vault_paths = writer.write_assembly_model(
                    placements=placements,
                    mass_props=mass_props,
                    interference_issues=interference_issues,
                    tool_access_results=tool_access_results,
                    disassembly_result=disassembly_result,
                    maintenance_summary=maintenance_summary,
                    trace_id=_trace_id,
                    run_id=_run_id,
                )
            except Exception as exc:
                vault_paths = []

        # Collect errors
        errors: list[str] = []
        errors.extend(i.description for i in interference_issues if i.severity == "error")
        errors.extend(r.description for r in tool_access_results if r.severity == "error")
        errors.extend(maintenance_summary.serviceability_warnings)
        if mass_props.over_budget:
            errors.append(
                f"[MASS OVERRUN] Total {mass_props.total_mass_kg:.3f} kg "
                f"> budget {mass_props.mass_budget_kg:.3f} kg"
            )

        return AssemblyReport(
            run_id=_run_id,
            trace_id=_trace_id,
            project=self._project,
            coordinate_system=coord_sys,
            placements=placements,
            mass_props=mass_props,
            interference_issues=interference_issues,
            tool_access_results=tool_access_results,
            disassembly_result=disassembly_result,
            maintenance_summary=maintenance_summary,
            vault_paths=vault_paths,
            has_errors=bool(errors),
            error_summary=errors,
        )

    def print_summary(self, report: AssemblyReport) -> None:
        """Print a concise summary to stdout."""
        p = report
        print(f"\n{'='*60}")
        print(f"ASSEMBLY REPORT — {p.project}")
        print(f"{'='*60}")
        print(f"Components placed:  {len(p.placements)}")
        print(f"Total mass:         {p.mass_props.total_mass_kg:.3f} kg")
        if p.mass_props.mass_budget_kg:
            print(f"Mass margin:        {p.mass_props.mass_margin_kg:+.3f} kg")
        print(f"CG:                 {p.mass_props.center_of_mass_mm}")
        print(f"Interference errors:{sum(1 for i in p.interference_issues if i.severity=='error')}")
        print(f"Tool access errors: {sum(1 for r in p.tool_access_results if r.severity=='error')}")
        print(f"\n{format_disassembly_table(p.disassembly_result)}")
        print(f"\n{format_maintenance_table(p.maintenance_summary)}")
        if p.error_summary:
            print("\nERRORS:")
            for e in p.error_summary:
                print(f"  ✗ {e}")
        else:
            print("\n✓ Assembly validated — ready for CAD export and system FEA")

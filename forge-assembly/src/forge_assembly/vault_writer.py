"""Write assembly results to the FORGE Obsidian vault — Step 9."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter
import yaml

from forge_assembly.disassembly import DisassemblyResult, format_disassembly_table
from forge_assembly.interference import InterferenceIssue
from forge_assembly.maintenance import MaintenanceSummary, format_maintenance_table
from forge_assembly.mass_props import MassProperties
from forge_assembly.placement import ComponentPlacement
from forge_assembly.tool_access import ToolAccessResult


class AssemblyVaultWriter:
    """Write the 5 assembly output notes to the FORGE vault."""

    def __init__(self, vault_root: Path, project_name: str) -> None:
        self._vault_root = vault_root
        self._project = project_name
        self._assembly_dir = vault_root / "01-Projects" / project_name / "assembly"
        self._assembly_dir.mkdir(parents=True, exist_ok=True)

    def _write_note(self, filename: str, metadata: dict[str, Any], body: str) -> Path:
        metadata["created"] = datetime.now(timezone.utc).isoformat()
        metadata["project"] = self._project
        post = frontmatter.Post(body, **metadata)
        path = self._assembly_dir / filename
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return path

    def write_assembly_model(
        self,
        placements: list[ComponentPlacement],
        mass_props: MassProperties,
        interference_issues: list[InterferenceIssue],
        tool_access_results: list[ToolAccessResult],
        disassembly_result: DisassemblyResult,
        maintenance_summary: MaintenanceSummary,
        trace_id: str,
        run_id: str,
    ) -> list[Path]:
        """Write all 5 assembly vault notes and return paths."""
        paths: list[Path] = []

        # Counts
        interference_errors = sum(1 for i in interference_issues if i.severity == "error")
        clearance_warnings = sum(1 for i in interference_issues if i.severity == "warning")
        tool_errors = sum(1 for r in tool_access_results if r.severity == "error")
        tool_warnings = sum(1 for r in tool_access_results if r.severity == "warning")

        # 1. assembly_model.md
        placement_table = "\n".join(
            f"| {p.component_id} | {p.name} | {p.translation_mm} | {p.mass_kg:.3f} |"
            for p in placements
        )
        cg = mass_props.center_of_mass_mm
        paths.append(self._write_note(
            "assembly_model.md",
            {
                "type": "assembly",
                "total_mass_kg": round(mass_props.total_mass_kg, 3),
                "mass_budget_kg": mass_props.mass_budget_kg,
                "mass_margin_kg": round(mass_props.mass_margin_kg or 0.0, 3),
                "CG_mm": [round(cg[0], 1), round(cg[1], 1), round(cg[2], 1)],
                "interference_errors": interference_errors,
                "clearance_warnings": clearance_warnings,
                "tool_access_errors": tool_errors,
                "tool_access_warnings": tool_warnings,
                "disassembly_cycles": 0,
                "L1_field_count": maintenance_summary.l1_count,
                "L2_depot_count": maintenance_summary.l2_count,
                "L3_factory_count": maintenance_summary.l3_count,
                "field_replaceable_fraction": round(
                    maintenance_summary.field_replaceable_fraction, 2
                ),
                "status": "validated" if interference_errors == 0 and tool_errors == 0 else "issues_found",
                "trace_id": trace_id,
                "run_id": run_id,
                "tags": ["assembly", "dfa", "validated"],
            },
            f"""# Assembly Model — {self._project}

## Coordinate System
- Origin: nose tip of fuselage
- X: aft, Y: starboard, Z: up (mm)

## Component Placements

| ID | Name | Translation (mm) | Mass (kg) |
|---|---|---|---|
{placement_table}

## Mass Budget
- Total mass: {mass_props.total_mass_kg:.3f} kg
- Budget: {mass_props.mass_budget_kg or 'N/A'} kg
- Margin: {mass_props.mass_margin_kg or 'N/A'} kg
- Center of mass: {cg}

## Status
- Interference errors: {interference_errors}
- Clearance warnings: {clearance_warnings}
- Tool access errors: {tool_errors}
""",
        ))

        # 2. interference_report.md
        iss_body = "\n".join(
            f"- **[{i.severity.upper()}]** {i.description}" for i in interference_issues
        ) or "_No interference or clearance issues detected._"
        paths.append(self._write_note(
            "interference_report.md",
            {"type": "assembly_interference", "error_count": interference_errors,
             "warning_count": clearance_warnings, "trace_id": trace_id},
            f"# Interference Report — {self._project}\n\n{iss_body}\n",
        ))

        # 3. tool_access_report.md
        ta_lines = [
            f"- **[{r.severity.upper()}]** {r.description}"
            for r in tool_access_results
            if r.severity in ("error", "warning")
        ]
        ta_body = "\n".join(ta_lines) or "_All fasteners have clear tool access._"
        paths.append(self._write_note(
            "tool_access_report.md",
            {"type": "assembly_dfa", "error_count": tool_errors,
             "warning_count": tool_warnings, "trace_id": trace_id},
            f"# DFA Tool Access Report — {self._project}\n\n{ta_body}\n",
        ))

        # 4. disassembly_sequence.md
        disasm_table = format_disassembly_table(disassembly_result)
        paths.append(self._write_note(
            "disassembly_sequence.md",
            {
                "type": "assembly_disassembly",
                "total_time_min": round(disassembly_result.total_estimated_time_min, 1),
                "non_destructive_count": disassembly_result.non_destructive_count,
                "total_component_count": disassembly_result.total_count,
                "trace_id": trace_id,
            },
            f"# Disassembly Sequence — {self._project}\n\n```\n{disasm_table}\n```\n",
        ))

        # 5. maintenance_access.md
        maint_table = format_maintenance_table(maintenance_summary)
        paths.append(self._write_note(
            "maintenance_access.md",
            {
                "type": "assembly_maintenance",
                "L1_field_count": maintenance_summary.l1_count,
                "L2_depot_count": maintenance_summary.l2_count,
                "L3_factory_count": maintenance_summary.l3_count,
                "field_replaceable_fraction": round(
                    maintenance_summary.field_replaceable_fraction, 2
                ),
                "warnings": len(maintenance_summary.serviceability_warnings),
                "trace_id": trace_id,
            },
            f"# Maintenance Access Classification — {self._project}\n\n```\n{maint_table}\n```\n",
        ))

        return paths

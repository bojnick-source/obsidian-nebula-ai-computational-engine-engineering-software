"""Jinja2 + WeasyPrint report renderer (Context 1B)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from forge_output.reports.assembler import ReportData

try:
    from weasyprint import HTML as WeasyHTML
    _WEASYPRINT_AVAILABLE = True
except ImportError:
    _WEASYPRINT_AVAILABLE = False


_TEMPLATES_DIR = Path(__file__).parents[4] / "templates"


class ReportRenderer:
    """Render ReportData to HTML and optionally PDF."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        tdir = templates_dir or _TEMPLATES_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(tdir)),
            autoescape=select_autoescape(["html", "j2"]),
        )

    def render_html(
        self,
        report_data: ReportData,
        template_name: str = "engineering_report.html.j2",
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        template = self._env.get_template(template_name)
        ctx: dict[str, Any] = {
            "report": report_data,
            "run_id": report_data.run_id,
            "trace_id": report_data.trace_id,
            "project": report_data.project,
            "task": report_data.task_description,
            "started_at": report_data.started_at,
            "completed_at": report_data.completed_at,
            "phases": report_data.phases_completed,
            "findings": report_data.agent_findings,
            "tool_results": report_data.tool_results,
            "gates": report_data.verification_gates,
            "debate_rounds": report_data.debate_rounds,
            "vault_notes": report_data.vault_notes_written,
            "total_tokens_in": report_data.total_tokens_in,
            "total_tokens_out": report_data.total_tokens_out,
            "total_cost_usd": report_data.total_cost_usd,
            "degraded_modes": report_data.degraded_modes_activated,
            "success": report_data.overall_success,
        }
        if extra_context:
            ctx.update(extra_context)
        return template.render(**ctx)

    def render_pdf(
        self,
        report_data: ReportData,
        output_path: Path,
        template_name: str = "engineering_report.html.j2",
    ) -> Path:
        if not _WEASYPRINT_AVAILABLE:
            raise RuntimeError(
                "WeasyPrint not installed. Install with: pip install weasyprint"
            )
        html_string = self.render_html(report_data, template_name)
        WeasyHTML(string=html_string).write_pdf(str(output_path))
        return output_path

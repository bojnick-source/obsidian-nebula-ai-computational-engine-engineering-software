# forge-output

Four output contexts for FORGE, all consuming from the single ZeroMQ event stream.

## Contexts

| Context | Description | Primary Tool |
|---|---|---|
| **1A: Live TUI** | Real-time pipeline visualization | Textual ≥0.90 |
| **1B: Report Generator** | Engineering PDF/HTML reports | Jinja2 + WeasyPrint |
| **1C: Vault Write-Back** | Obsidian note creation + Supermemory | python-frontmatter |
| **1D: Monitoring** | Structured logging + DuckDB + dashboards | structlog + DuckDB |

## Architecture

All contexts subscribe to the ZeroMQ PUB socket at `tcp://127.0.0.1:5555`.
None have direct access to the C++ core.

```
forge-core (ZMQ PUB)
  ├──▶ tui.py               (1A: Textual TUI)
  ├──▶ vault_writer.py      (1C: Obsidian + Supermemory)
  ├──▶ report_builder.py    (1B: assembled at run_complete)
  └──▶ event_logger.py      (1D: structlog → JSONL files)
```

## Structure

```
src/forge_output/
  event_consumer.py       # Base ZMQ SUB consumer
  event_schema.py         # Pydantic models for event types
  tui/
    app.py                # Textual ForgeApp
    widgets/              # Custom widgets (PipelineProgressBar, AgentStatusTable, etc.)
  reports/
    assembler.py          # Collects run data → ReportData
    renderer.py           # Jinja2 → HTML → WeasyPrint PDF
    math_renderer.py      # SymPy → LaTeX → KaTeX
    visualizations/
      pyvista_renderer.py # 3D stress/displacement plots (off-screen)
      matplotlib_plots.py # 2D convergence, S-N curves
      plotly_interactive.py # Interactive HTML elements
  vault/
    writer.py             # python-frontmatter + Supermemory
    auto_linker.py        # Entity registry + semantic linking
    dataview_queries.py   # Pre-built Obsidian Dataview queries
  monitoring/
    logging_config.py     # structlog configuration
    event_logger.py       # JSONL structured logger
    duckdb_queries.py     # Common DuckDB analytical queries
configs/
  report_templates.yaml   # Report type → template mapping
  entity_registry_seed.yaml # Seed entities for auto-linking
templates/
  engineering_report.html.j2  # Primary Jinja2 report template
  executive_summary.html.j2
  verification_section.html.j2
tests/
  test_event_consumer.py
  test_vault_writer.py
  test_report_renderer.py
```

## Quick Start (Week 1 target)

```bash
# Layer 1: JSONL logging only
python -m forge_output.monitoring.event_logger --zmq tcp://127.0.0.1:5555

# Layer 1+: Rich TUI prototype (before full Textual)
python -m forge_output.tui.proto --zmq tcp://127.0.0.1:5555
```

## Key Dependencies

```
textual>=0.90
rich>=13.0
pyzmq>=26.0
openlit>=1.0
watchfiles>=0.21
jinja2>=3.0
weasyprint>=60
pyvista>=0.47
meshio>=5.3
plotly>=5.0
sympy>=1.12
matplotlib>=3.8
python-frontmatter>=1.0
pyyaml>=6.0
structlog>=24.0
duckdb>=0.10
```

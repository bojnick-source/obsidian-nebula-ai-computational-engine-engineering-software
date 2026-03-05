# FORGE Textual TUI Spec (Context 1A)

> Live run presentation. Zero web infrastructure. Async-native. SSH-compatible.
> Implementation: Textual ≥0.90 (MIT, 20K GitHub stars, 120 FPS rendering).

---

## Layout: "Pipeline Waterfall + Active Focus"

```
┌─────────────────────────────────────────────────────────────────────┐
│ TOP BAR: 12-step pipeline progress indicator                        │
│  ✓ Intake  ✓ Route  ✓ Decompose  ✓ Memory  ► Specialist  ○ Tool... │
│  run_id: forge-042  │  elapsed: 4m23s  │  cost: $0.34  │  esc=quit │
├──────────────────────────────────┬──────────────────────────────────┤
│ LEFT: Agent Status Table         │ RIGHT: Active Focus              │
│                                  │                                  │
│ Agent              Step  Conf T  │ ► me_specialist (structural)     │
│ ────────────────────────────     │ ──────────────────────────────── │
│ ✓ librarian        4    0.9 2K  │ Analyzing motor mount bracket    │
│ ► me_specialist    5    0.8 4K  │ under 10N thrust load...         │
│   materials_antag  -    -   -   │                                  │
│   gmsh_wrapper     -    -   -   │ Given:                           │
│   calculix_wrapper -    -   -   │  • Material: 6061-T6 Al           │
│   struct_verifier  -    -   -   │  • E = 68.9 GPa, σ_y = 276 MPa  │
│   ...68 agents...               │  • Load: 10N at free end         │
│                                  │                                  │
│ [filter: active ▾]               │ Computing stress distribution... │
├──────────────────────────────────┴──────────────────────────────────┤
│ BOTTOM: Event log (filterable)                                      │
│  10:15:30 [BLACKBOARD] me_specialist wrote max_stress=~150MPa       │
│  10:15:28 [GATE] contract_gate PASS                                 │
│  10:15:25 [AGENT] me_specialist dispatched (domain=mech_eng)        │
│  [filter: all ▾]  [search: _______________]                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Textual Widget Map

### Top Bar: `PipelineProgressBar` (Custom Widget)
- Horizontal sequence of 12 labelled nodes
- State per step: `complete` (green ✓), `active` (yellow ► + spinner), `pending` (dim ○), `failed` (red ✗)
- Right side: run_id, elapsed time counter, live cost accumulator, keyboard shortcuts

### Left Panel: `AgentStatusTable` (DataTable)
- Columns: `status_emoji`, `agent_id`, `step`, `confidence`, `tokens` (total)
- Row color coding: green=active, gray=idle/pending, red=error, dim=complete
- Sortable by any column; filterable by status
- Updates at ~100ms intervals (batched, not per-token)

### Right Panel: `ActiveFocusLog` (RichLog)
- Streams reasoning tokens from whichever agent is currently active
- Tokens batched at 100ms intervals to avoid UI thrashing
- Syntax highlighting for equations, JSON, code blocks
- Shows last 200 lines; scrollable

### Solver Progress Inset (conditional — inside Right Panel when solver active)
- Activated when `tool_start` event for CalculiX or OpenFOAM received
- `Sparkline` widget: residual convergence plot (last 50 iterations)
- Shows: iteration count, displacement residual, energy residual
- Updates from file watcher on solver log files (`asyncio` inotify)

### Verification Gate Modal
- Triggered on `verification_gate` event
- Overlay shows: gate name, PASS/FAIL/WARN, error_code (if fail), confidence, principle checked
- Auto-dismisses after 3s on PASS; stays up on FAIL until acknowledged

### Bottom Panel: `EventLog` (DataTable)
- Filterable event log: all events, errors only, verification only
- Search box for text filter
- Color-coded by event type

---

## Solver-Specific Progress Metrics

| Solver | Progress Signal | Source |
|---|---|---|
| CalculiX | Iteration count + displacement residual | ccx stdout, tailed by file watcher |
| OpenFOAM | Residuals per timestep + Courant number | `logs/run.log`, tailed by file watcher |
| GMSH | Element count progress | gmsh Python API callback |
| FreeTO | Iteration + compliance + volume fraction | freeto stdout |

File watchers use `asyncio` with `inotify` on Linux. Updates are batched at 500ms intervals and fed to the Sparkline widget.

---

## `textual-web` Hybrid Mode

```bash
textual-web serve forge_tui:ForgeApp --port 8080
```

The same Textual app serves over the web with zero code changes. Useful for monitoring long-running analyses from a different machine without needing SSH.

---

## Key Dependencies

```toml
[project.dependencies]
textual = ">=0.90"
rich = ">=13.0"
pyzmq = ">=26.0"
openlit = ">=1.0"
watchfiles = ">=0.21"  # async file watching for solver logs
```

---

## Architecture Notes

- The TUI runs as a separate process subscribing to the ZMQ event stream — never in the C++ core's process
- If TUI crashes: core continues unaffected (PUB/SUB is fire-and-forget)
- All TUI state is derived from events — no direct API calls to core
- `textual-web` for remote monitoring without infrastructure

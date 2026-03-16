# FORGE — AI Computational Engineering Engine

**FORGE** is a multi-agent AI orchestration system for engineering-grade structural, aerodynamic, and multiphysics design and analysis. It combines a C++ orchestration runtime, a specialist/antagonist agent system, Obsidian-based neural memory, MCP-wrapped solvers, and a layered verification trust boundary.

---

## Program Structure

| Component | Description |
|---|---|
| **forge-core** | C++ orchestration spine: blackboard, routing, A2A/MCP dispatch |
| **forge_agent** | Python runtime layer: unified agent, intelligence router, MCP manager, token budget, skill router |
| **forge-agents** | Agent cards, prompts, registries (274 specialists, antagonists, verifiers, librarians) |
| **forge-assembly** | CAD assembly Python module: disassembly DAG, fasteners, maintenance, mass properties |
| **forge-learning** | Learning infrastructure: constitution, debate, discovery, evaluators, memory workflows |
| **forge-memory** | Obsidian neural memory (≥ v1.12): schemas, routing, synthesis, contradiction handling. NotebookLM pre-ingestion spec in `obsidian/notebooklm.md` |
| **forge-output** | Report generation, TUI, vault writer, DuckDB monitoring |
| **forge-tools** | MCP wrappers for solvers (CalculiX, GMSH, FreeTO, OpenFOAM, etc.) |
| **forge-verification** | Structural/adversarial/provenance/contradiction verifiers |
| **forge-tests** | Fixtures, goldens, red-team packs, integration scenarios |
| **forge-ops** | CI/CD, telemetry, security, cost tracking, incident response |
| **forge-vault** | Obsidian knowledge vault ≥ v1.12 (open in Obsidian; NotebookLM inbox + verified engineering notes) |
| **briefcase** | Node.js presentation layer: FORGE auto-ingest, LLM classification, Collections |
| **mesh-morph-lhs** | Parametric mesh morphing optimization engine (LHS sampling, geometry, simulation) |
| **external-ecosystem** | CAD/CFD/sim import bridges and validation gates |

## Active Projects

- **Aladdin-3B** — Smart fuselage structural design pipeline (current MVP focus)
- **Project Vanguard** — Structural/mechanism subassembly with controls integration
- **Phoenix Nigredo Dracenix** — Morphing configuration with plasma/magnetics interactions

## Build Lanes

| Lane | Scope |
|---|---|
| A | Planning canon (frozen docs, contracts, roadmap, risk, fixtures) |
| B | Core runtime spine (C++ skeleton → router → blackboard → orchestrator) |
| C | Memory core (intake/routing/gaps → advanced memory → thinking) |
| D | Agents & debate (specialist/antagonist/verifier/librarian + A2A) |
| E | Tool wrappers (GMSH/CalculiX/FreeTO first) |
| F | Verification trust boundary |
| G | Tests & red-team |
| H | Ops/observability |
| I | Project pipelines (Aladdin first) |
| J | R&D (RTSA, NVIDIA stack, digital twins) |

## Quick Links

- [Master Index](FORGE_MASTER_INDEX.md)
- [Current Catalog](docs/planning/catalog/forge-catalog-current.md)
- [MVP Spec](docs/planning/mvp/v0.1-spec.md)
- [Architecture Overview](docs/architecture/system-overview.md)

## Status

> **Phase:** Briefcase + Mesh-Morph Integration (Lanes A–D active)
> **Active Milestone:** v0.1 MVP Scaffold
> **Agent Count:** 274 agents (68 specialist↔antagonist pairs + system agents)
> **Catalog Version:** v8+
> **Obsidian Vault:** compatible with Obsidian ≥ v1.12 (current: v1.12.4)

## CI

All PRs run: `yamllint` → `ruff check` → `pytest`. All three must pass.

```
pip install pytest pytest-asyncio pyyaml ruff yamllint numpy python-frontmatter
pip install anthropic httpx asyncio-throttle watchdog fastmcp pydantic jinja2
pip install -e "forge_agent/[mcp]"
pip install -e forge-assembly/
pip install -e forge-output/
```

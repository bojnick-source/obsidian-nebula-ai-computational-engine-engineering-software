# CHANGELOG

All notable changes to the FORGE project.

## [0.1.0] — 2026-03-04

### Added
- Project initialization: Python MVP skeleton
- `forge.yaml` configuration: 7 agents, 3 providers, degraded memory mode
- `forge.py` CLI: boots, loads config, prints version, runs smoke test
- JSONL structured logging with trace IDs
- Blackboard: typed dict store for inter-agent communication
- Model router: provider selection, fallback chains, health tracking, budget gate
- 7 MVP agent definitions (SKILL.yaml, prompt.md, CHANGELOG.md each)
- Test suite: 23 tests covering config, blackboard, router, CLI
- 3 consolidated planning documents (FORGE_CATALOG.md, FORGE_EXECUTION_PLAN.md, DECISIONS.md)
- Planning freeze protocol in effect
- **Scaffolding skeleton** (Components A–L):
  - A. Core Runtime: `runtime.py` — PipelineRun, StepResult, 12-step loop init
  - B. Agent System: `agents/base.py` — BaseAgent ABC, AgentResult
  - C. Memory System: `memory/vault.py` — VaultStore, VaultNote
  - D. Tooling Layer: `tools/base.py` — ToolWrapper ABC, ToolResult
  - E. Verification Layer: `verification/` — structural checks, adversarial verdict
  - F. Data Contracts: `contracts.py` — AnalysisOutput, ToolResponse, TraceRecord
  - G. Observability & Ops: `observability.py` — ErrorCode enum, MetricsCounter
  - H. Build/Test Harness: `tests/fixtures/` — golden fixture YAML (cantilever beam)
  - I. Project Pipelines: `pipelines/registry.py` — PipelineSpec, PipelineRegistry
  - J. External Ecosystem Bridges: `bridges/base.py` — BaseBridge ABC, BridgeResult
  - K. Planning Corpus: verified existing docs
  - L. Recovery / Continuity: `recovery.py` — Snapshot, RecoveryManager

### Architecture Decisions
- ADR-001: Python for MVP (C++ deferred to V1-17)
- ADR-002: 7 agents for MVP (61 archived)
- ADR-003: Supermemory optional (Obsidian-only degraded mode)
- ADR-007: Planning freeze after master index

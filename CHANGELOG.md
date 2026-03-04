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

### Architecture Decisions
- ADR-001: Python for MVP (C++ deferred to V1-17)
- ADR-002: 7 agents for MVP (61 archived)
- ADR-003: Supermemory optional (Obsidian-only degraded mode)
- ADR-007: Planning freeze after master index

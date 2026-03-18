# FORGE GSD Roadmap

> Derived from tiered-roadmap.md. GSD phase numbering. Last updated: 2026-03-18.

| Phase | Name | Status | Branch |
|---|---|---|---|
| 1 | Briefcase Phase Implementation | ✓ VERIFIED 2026-03-17 | claude/briefcase-phase-implementation-gK4j5 |
| 2 | v0.1 MVP — Pipeline Integration + Acceptance Tests | ✓ VERIFIED 2026-03-18 | claude/briefcase-phase-implementation-gK4j5 |
| 3 | v0.1 Acceptance Gate (live solvers) | ✓ VERIFIED 2026-03-18 | claude/briefcase-phase-implementation-gK4j5 |
| 4 | V1 Build — Antagonist + A2A + Extended Tools | Planned | TBD |

## Phase 2 Milestones

- [x] Python pipeline runner (forge_agent/core/pipeline.py) — Lane I
- [x] Librarian Python runtime (forge_agent/agents/librarian.py) — Lane C
- [x] v0.1 Acceptance Test Suite (pytest, mocked tools) — Lane F
- [x] Missing test fixtures (phase_1_2, phase_1_3, golden/) — Lane F

## Phase 3 Milestones

- [x] LiveToolExecutor (forge_agent/core/live_tool_executor.py)
- [x] Degraded-mode acceptance tests (test_v01_acceptance_live.py)
- [x] Log completeness audit (test_log_completeness.py)
- [x] Fixture parametrization (test_fixture_schemas.py)
- [x] v0.1 milestone declared

## Key Frozen Interfaces

All contract docs are frozen (v1). No changes permitted without ADR.
See `docs/contracts/` for canonical versions.

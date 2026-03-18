# FORGE GSD Roadmap

> Derived from tiered-roadmap.md. GSD phase numbering. Last updated: 2026-03-18.

| Phase | Name | Status | Branch |
|---|---|---|---|
| 1 | Briefcase Phase Implementation | ✓ VERIFIED 2026-03-17 | claude/briefcase-phase-implementation-gK4j5 |
| 2 | v0.1 MVP — Pipeline Integration + Acceptance Tests | → CURRENT | claude/briefcase-phase-implementation-gK4j5 |
| 3 | v0.1 Acceptance Gate (live solvers) | Planned | TBD |
| 4 | V1 Build — Antagonist + A2A + Extended Tools | Planned | TBD |

## Phase 2 Milestones

- [ ] Python pipeline runner (forge_agent/core/pipeline.py) — Lane I
- [ ] Librarian Python runtime (forge_agent/agents/librarian.py) — Lane C
- [ ] v0.1 Acceptance Test Suite (pytest, mocked tools) — Lane F
- [ ] Missing test fixtures (phase_1_2, phase_1_3, golden/) — Lane F

## Key Frozen Interfaces

All contract docs are frozen (v1). No changes permitted without ADR.
See `docs/contracts/` for canonical versions.

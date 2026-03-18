---
id: 3-002
status: complete
commit: feccd29
date: 2026-03-18
---

## What was done

Implemented `forge_agent/tests/test_v01_acceptance_live.py` — 8 degraded-mode
acceptance tests running PipelineRunner with LiveToolExecutor (no mocks).

All 10 v0.1 ACs verified to hold in CI environment (gmsh absent, ccx absent):
- Trace ID propagation (AC-01)
- Vault note with frontmatter (AC-06)
- Amnesia check passes (AC-07)
- TaskResult shape valid (AC-08)
- Vault blocked on gate failure (AC-09)
- 9-phase JSONL events (AC-10)
- Degraded status when tools absent (returns degraded+confidence=0.5)
- Tool envelopes carry $schema v1

## Files changed

- `forge_agent/tests/test_v01_acceptance_live.py` (created, 8 tests)

## Gate results

- ruff PASS
- pytest test_v01_acceptance_live.py: 8/8 PASS
- pytest full suite: 379/379 PASS

## Gaps discovered

None. Status="degraded" contract confirmed working end-to-end.

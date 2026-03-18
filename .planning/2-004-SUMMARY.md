---
id: 2-004
title: Missing test fixtures — phase_1_2, phase_1_3, golden outputs
status: complete
date: 2026-03-18
---

## Outcome

All 4 fixture files were already committed to the branch as part of
`feat(2-002): LibrarianAgent — intake, retrieve, amnesia-check, gap detection`
(commit `ddbc68a`). No new commit was required for plan 2-004.

## Files Created (in commit ddbc68a)

| File | Status |
|---|---|
| `forge-tests/fixtures/phase_1_2/vault_write_readback.yaml` | Committed |
| `forge-tests/fixtures/phase_1_3/gap_detection_missing_fea.yaml` | Committed |
| `forge-tests/fixtures/golden/verifier_red_team/provenance_errors_golden.yaml` | Committed |
| `forge-tests/fixtures/golden/verifier_red_team/unit_errors_golden.yaml` | Committed |
| `forge-tests/FIXTURE_INDEX.md` | Updated with all 4 rows; phase_1_2 + phase_1_3 removed from Planned |

## yamllint Result

```
yamllint forge-tests/fixtures/phase_1_2/   → PASS
yamllint forge-tests/fixtures/phase_1_3/   → PASS
yamllint forge-tests/fixtures/golden/      → PASS
```

All new YAML files comply with `.yamllint.yml` (max line 120, 2-space list
indentation, no document-start requirement).

## pytest Result

```
342 passed in 4.43s
```

No regressions. The YAML fixture files are data-only and do not add new
pytest test cases (no corresponding test file reads them yet).

## Gaps Discovered

- No pytest test file currently loads `phase_1_2/`, `phase_1_3/`, or
  `golden/verifier_red_team/` fixture data. The fixtures are available for
  future test parameterization but are not exercised by the current suite.
  This is expected per plan 2-004 scope — fixtures are data only.
- A follow-on task should wire these fixtures into parameterized pytest
  cases (candidate plan: 2-005 or 2-006).

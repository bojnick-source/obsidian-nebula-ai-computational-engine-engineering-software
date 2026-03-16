Verify completed FORGE phase $ARGUMENTS against acceptance criteria.

## Invocation

```
/gsd:verify-work <N>
```

## Workflow

<workflow>

### 1 — Load context

Read:
- `.planning/REQUIREMENTS.md` — phase N acceptance criteria
- `.planning/<N>-*-SUMMARY.md` — what each plan claimed to do
- `CLAUDE.md` — P1-P11 known mistake patterns to check

### 2 — Run automated gates

```bash
ruff check . --ignore E501
yamllint .
pytest --tb=short -q
python tools/validate_registry.py
```

Report pass/fail for each gate.

### 3 — Acceptance criteria check

Spawn a verifier Task for each acceptance criterion:

```
Criterion: <criterion text>

Verify this is satisfied in the current codebase.
Use Read, Glob, Grep, Bash to check.
Return: PASS / FAIL / PARTIAL with evidence.
```

### 4 — Known mistake audit

Grep codebase for P1-P11 patterns from CLAUDE.md:
- P1: method names called on objects (AttributeError risk)
- P2: accepted-but-unused parameters
- P3: circuit breaker HALF_OPEN race condition
- P10: missing pyproject.toml for pip-installed sub-packages
- P11: wrong setuptools build backend

Report any violations found.

### 5 — Write verification report

Write `.planning/<N>-VERIFICATION.md`:

```markdown
# Phase N Verification — <date>

## Gate results
- ruff: PASS/FAIL
- yamllint: PASS/FAIL
- pytest: PASS/FAIL (<N> passed)
- registry: PASS/FAIL

## Acceptance criteria
| Criterion | Result | Evidence |
|---|---|---|
| ... | PASS | ... |

## Known mistake audit
<findings or "clean">

## Verdict
VERIFIED / GAPS FOUND

## Gaps (if any)
1. <gap description> — fix with: /gsd:execute-phase N --gaps-only
```

### 6 — Report

Print verdict and next command:
- If VERIFIED: `/gsd:plan-phase N+1`
- If GAPS: `/gsd:execute-phase N --gaps-only`

</workflow>

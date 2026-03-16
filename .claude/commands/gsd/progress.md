Show current FORGE project status and next steps.

## Workflow

<workflow>

Read in parallel:
- `.planning/STATE.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- All `.planning/*-VERIFICATION.md` files
- `git log --oneline -20`

Print a status report:

```
━━━ FORGE PROJECT STATUS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current phase : N — <phase name>
Branch        : <current git branch>

ROADMAP
  Phase 1 ✓  <name>
  Phase 2 ✓  <name>
  Phase 3 →  <name>  ← current
  Phase 4    <name>

PHASE N PLANS
  ✓ plan-001  <title>  (<commit SHA>)
  ✓ plan-002  <title>  (<commit SHA>)
  ✗ plan-003  <title>  (not started)

VERIFICATION
  <result from VERIFICATION.md if exists, else "not yet verified">

GAPS
  <list gaps or "none">

RECENT COMMITS
  <git log --oneline -10>

━━━ NEXT STEPS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /gsd:execute-phase N        — run remaining plans
  /gsd:execute-phase N --gaps-only  — fix gaps only
  /gsd:verify-work N          — run acceptance tests
  /gsd:plan-phase N+1         — plan the next phase
  /gsd:quick <task>           — one-off task with commit
```

</workflow>

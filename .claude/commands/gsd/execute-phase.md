Execute FORGE phase $ARGUMENTS with wave-based parallelisation.

## What this does

Reads all PLAN.md files for the requested phase, groups them into dependency
waves, and executes each wave with fresh-context subagents. Every completed
plan gets its own atomic git commit.

Orchestrator uses ~15% of token budget. Each executor gets ~100% fresh context.

## Invocation

```
/gsd:execute-phase <N>
/gsd:execute-phase <N> --gaps-only
```

`--gaps-only` restricts execution to plans marked `gap_closure: true` (used
after `/gsd:verify-work` identifies fixes needed).

## Workflow

<workflow>

### 1 — Parse arguments

Extract phase number N from $ARGUMENTS. If omitted, read
`.planning/STATE.md` to find the current active phase.

If `--gaps-only` flag present, set GAP_MODE=true.

### 2 — Discover plans

Glob `.planning/<N>-*-PLAN.md`. For each plan file read:
- `id:` field
- `depends_on:` list
- `gap_closure:` boolean (filter if GAP_MODE)

If no plans found, print "No plans found for phase N" and stop.

### 3 — FORGE context check

Read `forge_agent/config/forge.yaml` for project context.
Read `.planning/REQUIREMENTS.md` for phase scope.
Read `CLAUDE.md` Conventions section — enforce branch pattern
`claude/<description>-<SESSION_ID>` before any commits.

### 4 — Build dependency waves

Topological sort on `depends_on` graph → list of waves.
Plans in the same wave have no interdependencies and run in parallel.

Print wave plan:
```
Wave 1 (parallel): plan-001, plan-002
Wave 2 (sequential): plan-003
```

### 5 — Execute waves

For each wave, spawn one Task agent per plan with this prompt:

```
You are executing FORGE plan: <plan_id>

Read the full plan: .planning/<N>-<plan_id>-PLAN.md

FORGE context:
- Registry: forge_agent/config/forge.yaml
- Branch: claude/<description>-<SESSION_ID>
- Allowed languages: C++ (core), Python (MCP/tools), MATLAB (topo-opt), GPU/CUDA (physics)
  See CLAUDE.md Polyglot Architecture Doctrine — no other languages.

Implement all tasks in the plan. When complete:
1. Run: ruff check . --ignore E501
2. Run: yamllint .
3. Run: pytest --tb=short -q
4. If all pass → git add <changed files> && git commit -m "<plan_id>: <summary>"
5. Write .planning/<N>-<plan_id>-SUMMARY.md with: what was done, files changed,
   gate results, and any gaps discovered.
```

Wait for all agents in the wave to complete before starting the next wave.

### 6 — Checkpoint after each wave

After each wave: read all SUMMARY.md files produced. If any agent reported
a hard failure (no commit made), pause and print the failure details.
Ask: "Continue to next wave? (yes/no)"

### 7 — Phase verification

After all waves complete, run automated verification:

```
Spawn Task agent:
  Read .planning/REQUIREMENTS.md phase N section.
  Read all .planning/<N>-*-SUMMARY.md files.
  Check: does the codebase satisfy all acceptance criteria?
  List any gaps found.
  Write .planning/<N>-VERIFICATION.md with verdict and gap list.
```

### 8 — State update

Append to `.planning/STATE.md`:
```
## Phase N — Completed <date>
Plans executed: <list>
Gaps: <list or "none">
Next: /gsd:plan-phase <N+1>
```

### 9 — Report

Print summary:
- Plans executed and their commit SHAs
- Verification verdict
- Gaps requiring attention
- Next command: `/gsd:verify-work N` or `/gsd:plan-phase N+1`

</workflow>

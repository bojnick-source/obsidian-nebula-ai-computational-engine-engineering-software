Execute a quick FORGE task with GSD guarantees: atomic commit, state tracking.

## Invocation

```
/gsd:quick <task description>
/gsd:quick <task description> --discuss
/gsd:quick <task description> --research
/gsd:quick <task description> --full
```

Flags:
- `--discuss` — surface assumptions before executing
- `--research` — investigate approach before executing
- `--full` — plan + verify + execute (full quality guarantees)

Use default (no flags) when you know exactly what to do.

## Workflow

<workflow>

### 1 — Parse task

Extract task description and flags from $ARGUMENTS.
Read `CLAUDE.md` — apply polyglot doctrine and known mistake patterns.

### 2 — Discuss (if --discuss)

Ask 2-3 clarifying questions to surface ambiguities.
Print assumptions and get confirmation before proceeding.

### 3 — Research (if --research)

Spawn a focused research Task:
```
Research: <task description>

Search codebase with Glob/Grep.
Identify: existing patterns, relevant files, implementation approach.
List potential pitfalls (cross-reference CLAUDE.md P1-P11).
Return findings in ≤300 words.
```

### 4 — Plan (if --full)

Write `.planning/quick/<task-slug>-PLAN.md` with:
- Objective
- Acceptance criteria
- Implementation steps
- Files to change
- Verification gates

### 5 — Execute

Spawn an executor Task:

```
Task: <task description>
Research: <research output if --research>
Plan: <plan file if --full>

FORGE constraints:
- Languages: C++ (core), Python (tools/MCP), MATLAB (topo-opt), GPU (physics)
  No other languages — see CLAUDE.md Polyglot Architecture Doctrine.
- CLI dispatch is primary (forge_agent/core/cli_dispatcher.py)
  MCP is fallback (forge_agent/core/mcp_manager.py)
- Known mistakes to avoid: P1-P11 in CLAUDE.md

Implement the task. When done:
1. ruff check . --ignore E501
2. yamllint .
3. pytest --tb=short -q
4. git add <changed files>
5. git commit -m "quick: <task description>"

Report: files changed, commit SHA, gate results.
```

### 6 — Verify (if --full, max 1 iteration)

Check the commit against acceptance criteria from the plan.
If gaps found, spawn a single fix pass.

### 7 — State update

Append to `.planning/STATE.md` Quick Tasks table:
```
| <date> | <task description> | <commit SHA> | done |
```

Write `.planning/quick/<task-slug>-SUMMARY.md` with:
- What was done
- Commit SHA
- Gate results

### 8 — Report

Print: task completed, commit SHA, files changed.

</workflow>

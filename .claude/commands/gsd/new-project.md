Initialise or re-initialise FORGE project planning structure.

## Invocation

```
/gsd:new-project
/gsd:new-project --auto
```

`--auto` skips interactive questions (expects project idea in $ARGUMENTS).

## Workflow

<workflow>

### 1 — Load existing context

Read (if they exist):
- `forge_agent/config/forge.yaml` — FORGE project config
- `CLAUDE.md` — conventions, polyglot doctrine, phase structure
- `docs/architecture/` — any existing ADRs

### 2 — Gather project info (skip if --auto)

Ask:
1. What is the primary engineering problem FORGE is solving for this project?
2. Which FORGE agent domains are in scope? (aerodynamics, structures, thermal, etc.)
3. What are the output deliverables? (STL, FEA report, optimised geometry, ...)
4. What is the target timeline / milestone structure?

### 3 — Create .planning/ structure

Write the following files:

**.planning/PROJECT.md**
```markdown
# FORGE Project: <name>

## Vision
<one-paragraph description>

## Engineering domains
<list from forge.yaml agent registry>

## Polyglot stack
- C++: core runtime, blackboard, model router, orchestration
- Python: MCP servers, vault interface, specialist agents
- MATLAB: FreeTO topology optimisation, Swan level-set
- GPU: Warp physics, PhysX (when simulation required)

## Key constraints
<from CLAUDE.md and forge.yaml>
```

**.planning/REQUIREMENTS.md**
```markdown
# Requirements

## Phase 1: <name>
### Goals
### Acceptance criteria
### Out of scope

## Phase 2: <name>
...
```

**.planning/ROADMAP.md**
```markdown
# Roadmap

| Phase | Name | Key deliverables | Dependencies |
|---|---|---|---|
| 1 | | | |
| 2 | | | 1 |
```

**.planning/STATE.md**
```markdown
# Project State

Current phase: 1
Last updated: <date>

## Quick Tasks Completed
| Date | Task | Commit | Status |
|---|---|---|---|
```

**.planning/config.json**
```json
{
  "project": "<name>",
  "forge_yaml": "forge_agent/config/forge.yaml",
  "branch_pattern": "claude/<description>-<SESSION_ID>",
  "cli_first": true,
  "mcp_fallback": true,
  "polyglot_doctrine": "CLAUDE.md"
}
```

### 4 — Report

Print:
- Files created
- Detected phase structure
- Next command: `/gsd:plan-phase 1`

</workflow>

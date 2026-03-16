Research, plan, and verify FORGE phase $ARGUMENTS.

## Invocation

```
/gsd:plan-phase <N>
/gsd:plan-phase <N> --skip-research
/gsd:plan-phase <N> --gaps
/gsd:plan-phase <N> --skip-verify
```

Flags:
- `--skip-research` — skip domain research, go straight to planning
- `--gaps` — gap closure mode: read VERIFICATION.md, plan fixes only
- `--skip-verify` — produce plans without verification loop

## Workflow

<workflow>

### 1 — Parse arguments

Extract phase number N and flags from $ARGUMENTS.
If N is omitted, read `.planning/STATE.md` → current phase.

### 2 — Load context

Read in parallel:
- `forge_agent/config/forge.yaml` — project + agent registry
- `.planning/PROJECT.md` — vision
- `.planning/REQUIREMENTS.md` — all phases; focus on phase N
- `.planning/ROADMAP.md` — milestone structure
- `.planning/STATE.md` — current progress
- `CLAUDE.md` — conventions, polyglot doctrine, known mistake patterns

If `--gaps` flag: also read `.planning/<N>-VERIFICATION.md` for gap list.

### 3 — Domain research (skip if --skip-research or --gaps)

Identify the engineering domains required for phase N from REQUIREMENTS.md.

For each domain, spawn a parallel research Task:

```
Research domain: <domain> for FORGE phase N

Questions to answer:
1. What are the best-practice implementation patterns in this domain?
2. What are the known failure modes and how to avoid them?
3. What tools/libraries are available in the FORGE polyglot stack?
   (C++ core, Python MCP, MATLAB topo-opt, GPU physics — no other languages)
4. What verification approach should be used?

Search the codebase (Glob/Grep) and web (WebFetch) as needed.
Write findings to .planning/<N>-research-<domain>.md
```

Wait for all research agents to complete.

### 4 — Generate plans

Spawn a planner Task agent with full context:

```
You are the FORGE phase N planner.

Context files (read all):
- .planning/PROJECT.md
- .planning/REQUIREMENTS.md (phase N section)
- .planning/ROADMAP.md
- .planning/<N>-research-*.md (all research outputs)
- CLAUDE.md (conventions + known mistake patterns P1-P11)

Generate one PLAN.md file per logical work unit. Each file:

File name: .planning/<N>-<id>-PLAN.md
Required fields:
  id: <short-id>
  phase: <N>
  title: <one line>
  depends_on: [<id>, ...]  # or []
  gap_closure: false        # true only for --gaps mode plans
  language: <C++|Python|MATLAB|GPU>  # per polyglot doctrine

Body sections:
  ## Objective
  ## Acceptance criteria (testable)
  ## Implementation steps
  ## Files to create / modify
  ## Verification gates (ruff / yamllint / pytest commands)
  ## Known risk (reference P1-P11 from CLAUDE.md if applicable)

Constraints:
- Every plan must have ≥1 pytest-verifiable acceptance criterion.
- No plan may introduce a language not in CLAUDE.md polyglot table.
- Plans with shared dependencies must declare them in depends_on.
```

### 5 — Verify plans (skip if --skip-verify)

Spawn a verifier Task (max 2 iterations):

```
Read all .planning/<N>-*-PLAN.md files.
Read .planning/REQUIREMENTS.md phase N acceptance criteria.

Check each plan:
1. Does it address a real requirement?
2. Are acceptance criteria testable (not vague)?
3. Are dependencies correct (no cycles)?
4. Does it respect the polyglot doctrine?
5. Does it guard against P1-P11 known mistakes?

For each issue found: note the plan file and exact fix required.
If issues found, return them. If clean, return "VERIFIED".
```

If verifier returns issues, pass them back to the planner (iteration 2).
After iteration 2, accept the plans as-is and note remaining issues.

### 6 — State update

Append to `.planning/STATE.md`:
```
## Phase N — Planned <date>
Plans: <list of plan IDs>
Research: <list of domain files>
Ready for: /gsd:execute-phase N
```

### 7 — Report

Print:
- List of generated PLAN.md files with one-line summaries
- Dependency wave preview (which plans can run in parallel)
- Verification result
- Next command: `/gsd:execute-phase N`

</workflow>

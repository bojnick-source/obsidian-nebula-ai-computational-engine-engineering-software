# Copilot Instructions — FORGE

These instructions apply to all code suggestions, PR reviews, and completions in this repository.

---

## Project Overview

FORGE is a multi-agent AI orchestration system for engineering analysis. It has two runtime layers:
- `forge_agent/` — Python runtime (orchestration, routing, MCP, memory)
- `forge-core/` — C++ spine (blackboard, event bus, dispatcher)

Agent metadata lives in `forge-agents/` (YAML cards + SKILL.md files, NOT runtime code).

---

## Python Code Rules

### Async / Sync

- Never mix sync and async without explicit adapters. If a server method calls a manager method, both must match: all-async or all-sync.
- When wrapping an async function synchronously, use `asyncio.run()` or a dedicated event loop — never `loop.run_until_complete()` if a loop may already be running.
- Always verify that every method called on an object exists on that class with the correct signature before writing the call.

### Function Parameters

- Never accept a parameter that has zero code paths reading it. Either use the parameter or remove it from the signature.
- If a parameter is optional and unused in a scaffold, add a `# TODO: use <param>` comment or raise `NotImplementedError`.

### Concurrency / Thread Safety

- Circuit breakers in `HALF_OPEN` state must allow exactly ONE probe request. Use a boolean flag (`_probe_in_flight`) cleared only after `record_success()` or `record_failure()`.
- Do not assume `dict` operations are atomic in threaded contexts — use locks.

### Error Handling

- Use error codes from `docs/contracts/error-codes.md` verbatim. Do not invent inline error code strings.
- Never use bare `except:` — always catch a specific exception type.
- Do not swallow exceptions silently. At minimum log them.

---

## YAML Rules

### Agent Cards

- All list items in agent card YAML must use 2-space indentation: `  - item` (not 4-space).
- Agent IDs: `snake_case` only. Suffix must be `_specialist` or `_antagonist` for domain agents.
- Do not add extra top-level keys not in the agent card schema.

### GitHub Actions Workflows

- The `on:` top-level key is excluded from yamllint via `.yamllint.yml`. Do not quote it unless moving the file outside `.github/workflows/`.
- Keep all `run:` shell lines under 120 characters. Use `\` continuation for long strings.
- Never add `|| true` to lint or test steps. Failures must be visible and block CI.

### General YAML

- Run `yamllint .` (uses `.yamllint.yml` — max line 120, excludes `.github/workflows/`) before committing.
- Quoted strings in YAML: use `"double quotes"` for strings that contain special characters or are numbers/booleans.

---

## CI Requirements

All PRs must pass:

1. `yamllint .` — zero errors, zero warnings
2. `ruff check . --ignore E501` — zero errors
3. `pytest --tb=short -q` — zero collection errors, all tests pass

**Never merge a PR with `|| true` masking failures.**

---

## Relative Links in Markdown

Count directory depth carefully:

| File location | Root is |
|---|---|
| `docs/planning/catalog/*.md` | `../../../` |
| `docs/planning/mvp/*.md` | `../../../` |
| `docs/architecture/*.md` | `../../` |
| `docs/contracts/*.md` | `../../` |

---

## Known Past Bugs — Watch For These

When reviewing PRs or generating code, actively check for:

| # | Pattern | Where to check |
|---|---|---|
| 1 | Server calls methods that don't exist on manager class | Any new server/manager pair |
| 2 | Function parameter accepted but never read | All function signatures |
| 3 | `HALF_OPEN` circuit breaker allows multiple concurrent probes | `retry.py`, any CB implementation |
| 4 | `|| true` silencing CI failures | `.github/workflows/*.yml` |
| 5 | YAML list items with 4-space indent instead of 2 | Agent cards, config YAML |
| 6 | Error codes not in `docs/contracts/error-codes.md` | Any error string |
| 7 | Broken relative markdown links (wrong `../` depth) | Docs referencing root files |
| 8 | Retry count stated ambiguously ("retry 3x" vs "4 total attempts") | Docs, retry configs |

---

## Testing

- Tests live in: `tests/`, `forge_agent/tests/`, `tools/tests/`, `forge-assembly/tests/`, `forge-output/tests/`
- Use `pytest.mark.asyncio` for async tests — requires `pytest-asyncio` installed.
- Do not import optional dependencies at module level if they may not be installed in all environments. Use lazy imports inside functions.

---

## File Naming

- Python modules: `snake_case.py`
- Agent directories: `snake_case/` (matching agent ID)
- SKILL.md: minimum 60 lines, exactly 8 `##` section headings
- Branch pattern: `claude/<short-description>-<SESSION_ID>`

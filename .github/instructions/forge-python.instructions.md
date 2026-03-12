---
applyTo: "**/*.py"
---

# FORGE — Python Coding Instructions

## Async / Sync Rules

- Never mix sync and async without explicit adapters. If a server calls methods on a manager,
  both must match — all-async or all-sync.
- Always verify that every method called on an object actually exists on that class with the
  correct sync/async signature before writing the call.
- When wrapping async code synchronously, use `asyncio.run()` — never `loop.run_until_complete()`
  if a loop may already be running.

## Function Parameters

- Never accept a parameter with zero code paths that read it. Either use it or remove it.
- If a parameter is intentionally unused in a scaffold, add `# TODO: use <param>` or raise
  `NotImplementedError`.

## Concurrency / Thread Safety

- Circuit breakers in `HALF_OPEN` state must allow exactly ONE probe request. Use a boolean
  flag (`_probe_in_flight`) cleared only after `record_success()` or `record_failure()`.
- Never assume `dict` operations are atomic in threaded contexts — use locks.
- asyncio.create_task() calls must always store a reference:
  ```python
  task = asyncio.create_task(coro())
  self._pending_tasks.append(task)   # never drop silently
  ```

## Import Style

- New code imports infrastructure from `forge_agent.core.*`:
  - `from forge_agent.core.verifier import VerifierAgent`
  - `from forge_agent.core.multi_agent_orchestrator import MultiAgentOrchestrator`
- The old `agents/verifier.py`, `agents/multi_agent_orchestrator.py`, `agents/orchestrator.py`
  are redirect shims or deprecated — do not add new imports pointing to them.

## Error Handling

- Use error codes from `docs/contracts/error-codes.md` verbatim.
- Never use bare `except:` — always catch a specific exception type.
- Do not swallow exceptions silently. At minimum log them.
- Re-raise after logging if the caller needs to know: `raise`.

## Module Naming

- Agent persona files use full descriptive names: `mechanical_engineer.py`, not `me.py`.
- Core infrastructure modules live in `forge_agent/core/`.
- Domain agent configs live in `forge_agent/agents/{category}/`.

## Known Past Bugs — Check For These in Every PR

| # | Pattern | File to Check |
|---|---|---|
| 1 | Server calls method that doesn't exist on manager | Any new server/manager pair |
| 2 | Parameter accepted but never read | All new function signatures |
| 3 | `HALF_OPEN` circuit breaker allows multiple concurrent probes | Any CB implementation |
| 4 | `asyncio.create_task()` without storing reference | Any vault/background write |
| 5 | Lazy import in `unified_agent.py` pointing to old/deprecated module path | `core/unified_agent.py:341` area |

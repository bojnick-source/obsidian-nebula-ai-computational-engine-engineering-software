---
id: 3-001
status: complete
commit: 790fb14
date: 2026-03-18
---

## What was done

Implemented `LiveToolExecutor` in `forge_agent/core/live_tool_executor.py`.

- `run_gmsh()`: attempts `import gmsh`; on ImportError (CI environment),
  returns `error_envelope(..., status="degraded", error_code="ERR_TOOL_SUBPROCESS_FAIL")`.
  Checks `geo_file` existence. On success, runs full gmsh mesh pipeline.
- `run_calculix()`: checks `shutil.which("ccx") or shutil.which("ccx_2.22")`;
  on None (CI environment), returns `error_envelope(..., status="degraded")`.
  On ccx available + file exists, runs subprocess via `asyncio.run(_run_ccx())`.
- Both methods: `task_id` written to `metadata` dict (P2 guard).
- Auto-generate `invocation_id` with `uuid.uuid4()` if caller omits it.
- `status="degraded"` (not `"error"`) on absent-tool paths — required for
  `PipelineRunner` pipeline.py:437 to set `blackboard["tool_execution.degraded"]`.

## Files changed

- `forge_agent/core/live_tool_executor.py` (created, 220 lines)
- `forge_agent/tests/test_live_tool_executor.py` (created, 15 tests)

## Gate results

- ruff PASS
- pytest forge_agent/tests/test_live_tool_executor.py: 15/15 PASS
- pytest full suite: 371/371 PASS

## Gaps discovered

None. All ACs pass. The `run_gmsh_subprocess` alias (forward-compatibility) was
added but is not required by any plan — harmless.

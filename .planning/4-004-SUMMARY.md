# 4-004 Summary: OpenFOAM and SU2 CLI Wrappers

## What Was Done

Created OpenFOAM and SU2 MCP wrapper servers following the existing gmsh/calculix pattern:

- `openfoam_server.py`: detects `foamRun` (v11+) or `simpleFoam`; returns `status="degraded"` +
  `error_code="ERR_TOOL_SUBPROCESS_FAIL"` when absent; `task_id` appended to `metadata` (P2);
  log.simpleFoam parsed for residuals and convergence when binary present.
- `su2_server.py`: detects `SU2_CFD`; same degraded pattern; `history.csv` parsed for CL/CD
  with case-insensitive column lookup (handles SU2 v7/v8 differences).
- `cli_dispatcher.py`: `openfoam_run` and `su2_run` handlers registered via `@_register`.
- `pipeline.py`: `DefaultToolExecutor.run_openfoam()` and `run_su2()` added with binary
  detection and degraded return matching calculix pattern.

## Files Changed

| Action | File |
|---|---|
| CREATE | `forge_agent/mcp_wrappers/openfoam_server.py` |
| CREATE | `forge_agent/mcp_wrappers/su2_server.py` |
| CREATE | `forge_agent/tests/test_openfoam_su2_wrappers.py` |
| MODIFY | `forge_agent/core/cli_dispatcher.py` — openfoam_run + su2_run handlers |
| MODIFY | `forge_agent/core/pipeline.py` — run_openfoam() + run_su2() in DefaultToolExecutor |

## Gate Results

```
pytest forge_agent/tests/test_openfoam_su2_wrappers.py -v: 12 passed
pytest --tb=short -q (full suite): 425 passed
ruff check openfoam_server.py su2_server.py --ignore E501: 0 errors
```

## Gaps

None.

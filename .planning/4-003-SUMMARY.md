# 4-003 Summary: Provider Failover Intelligence Router

## What Was Done

Added `FailoverRouter` class to `forge_agent/core/intelligence_router.py`:
- Anthropic→OpenAI automatic failover using per-provider `CircuitBreaker`
- `route_call(role, messages, **kwargs)` async — tries primary (Anthropic),
  falls back to secondary (OpenAI) on exception or OPEN/HALF_OPEN circuit
- `route_call_sync()` bridge for sync callers (avoids nested asyncio.run)
- Both `_primary_cb` and `_secondary_cb` injectable for testing
- HALF_OPEN probe guard: second concurrent caller skips primary, goes to secondary (P3)
- Both providers fail → `RuntimeError("ERR_PROVIDER_UNAVAILABLE ...")` (P7)

`PipelineRunner.__init__` gains optional `intelligence_router: Any = None` param:
- When set, `_run_phase_specialist()` calls `router.route_call_sync()` instead of direct Anthropic client
- Legacy `anthropic_client` path preserved when router is None (backward compatible)

## Files Changed

| Action | File |
|---|---|
| MODIFY | `forge_agent/core/intelligence_router.py` — FailoverRouter appended (165 lines) |
| MODIFY | `forge_agent/core/pipeline.py` — intelligence_router param + specialist path |
| MODIFY | `forge_agent/tests/test_intelligence_router.py` — 7 new FailoverRouter tests (AC 2-8) |

## Gate Results

```
pytest forge_agent/tests/test_intelligence_router.py: 21 passed
pytest --tb=short -q (full suite): 425 passed
ruff check forge_agent/core/intelligence_router.py --ignore E501: 0 errors
```

## Gaps

None.

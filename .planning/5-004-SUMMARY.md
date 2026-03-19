---
id: 5-004
phase: 5
title: Actuator safety specialist + antagonist Python agents
status: complete
completed: 2026-03-19
commit: a2cc4ed
---

## What Was Built

Three files implementing the `actuator_safety` domain for the Void Vanguard project:

### `forge_agent/agents/vanguard/actuator_safety.py`
- `ROLE = "actuator_safety_specialist"`
- `MODEL = "claude-opus-4-6"`
- `TEMPERATURE = 0.1` (lower than standard — safety analysis needs minimal variation)
- `SYSTEM_PROMPT` covering McKibben PAM safety analysis, QP filter design, state machine
  verification, mandatory thresholds (safety factor ≥ 2.0, burst ≥ 2× operating), and
  required output fields.

### `forge_agent/agents/vanguard/actuator_safety_antagonist.py`
- `ActuatorSafetyAntagonist(AntagonistAgent)` with heuristic `_generate_critique()`.
- Logic order (priority):
  1. `safety_factor` absent → `severity="fatal"` (provenance critique)
  2. `safety_factor < 2.0` → `severity="fatal"` (dimensional critique)
  3. `burst_pressure_kPa` absent → `severity="warning"` (provenance critique)
  4. All primary checks pass → `severity="info"` (methodology critique, checks failure mode coverage)
- P2 guard: `context` is explicitly consumed via `_ = context`.
- All returned dicts include required keys: `error_code`, `critique_type`, `severity`,
  `detail` (≥50 chars), `evidence`, `confidence_delta` (≤ 0.0).

### `forge_agent/tests/test_vanguard_actuator_safety.py`
- 8 tests covering all 9 acceptance criteria (AC1 is implicit — tests run without error).
- AC2: subclass check; AC3: empty dict → fatal; AC4: sf=1.5 → fatal; AC5: sf=2.5,
  no burst → warning; AC6: full output → info; AC7: SYSTEM_PROMPT contains "safety";
  AC8: ROLE constant; AC9: both params consumed.

## Verification Results

```
ruff check ... --ignore E501  →  All checks passed
pytest forge_agent/tests/test_vanguard_actuator_safety.py -v  →  8 passed
pytest --tb=short -q  →  469 passed
```

## P-Guard Compliance

| Guard | Status |
|---|---|
| P1 — interface mismatch | PASS — `AntagonistAgent.__init__(agent_id, domain)` and `_generate_critique` signature match |
| P2 — silently ignored params | PASS — `specialist_output` fully inspected; `context` consumed via `_ = context` |
| P7 — error codes | PASS — `error_code=None` (no invented error codes) |

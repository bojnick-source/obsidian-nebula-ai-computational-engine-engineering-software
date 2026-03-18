---
id: 4-001
title: AntagonistAgent base class
status: complete
date: 2026-03-18
---

## What Was Done

Implemented the `AntagonistAgent` abstract base class and its companion test suite
as specified in the 4-001 plan.

## Files Changed

| Action | File |
|---|---|
| CREATE | `forge_agent/agents/antagonist_base.py` |
| CREATE | `forge_agent/tests/test_antagonist_base.py` |

### `forge_agent/agents/antagonist_base.py`

- `CritiqueResult` dataclass with 6 fields matching the contract spec.
- `VALID_CRITIQUE_TYPES = frozenset({"factual", "dimensional", "provenance", "methodology"})`.
- `VALID_SEVERITIES = frozenset({"fatal", "warning", "info"})`.
- `AntagonistAgent(ABC)` with `__init__(agent_id, domain)`, public `critique()`,
  abstract `_generate_critique()`, and private `_validate()`.
- `_validate()` enforces: all 6 keys present, `critique_type` in valid set,
  `severity` in valid set, `detail` is `str` with `len >= 50`,
  `confidence_delta` is numeric and `<= 0.0`. Returns a normalised plain `dict`.
- P2 guard: both `specialist_output` and `context` forwarded into
  `_generate_critique()`; `agent_id` and `domain` stored as instance attributes.
- P7 guard: `error_code` is `str | None` — base class never invents codes.

### `forge_agent/tests/test_antagonist_base.py`

9 test cases via `ConcreteAntagonist` fixture:

1. `test_critique_returns_required_fields` — all 6 keys present.
2. `test_severity_in_valid_set` — "fatal", "warning", "info" each accepted.
3. `test_invalid_severity_raises` — "critical" raises `ValueError`.
4. `test_confidence_delta_le_zero` — 0.0 and negatives accepted.
5. `test_positive_confidence_delta_raises` — 0.1 raises `ValueError`.
6. `test_detail_min_length_enforced` — 49-char detail raises `ValueError`.
7. `test_detail_at_boundary_accepted` — 50-char detail accepted.
8. `test_missing_key_raises` — omitting "evidence" raises `ValueError`.
9. `test_both_params_consumed` — `specialist_output` and `context` both reach
   `_generate_critique()` (P2 verification via instance attribute inspection).

## Gate Results

| Gate | Result |
|---|---|
| `ruff check forge_agent/agents/antagonist_base.py --ignore E501` | PASS (0 errors) |
| `ruff check forge_agent/tests/test_antagonist_base.py --ignore E501` | PASS (0 errors) |
| `pytest forge_agent/tests/test_antagonist_base.py -v` | PASS (9/9) |
| `pytest --tb=short -q` (full suite) | PASS (398/398) |

## Gaps / Out of Scope

- None of the 111 antagonist YAML cards have Python implementations yet.
  This plan creates only the abstract base. Concrete subclasses will be introduced
  in a later wave when individual antagonist agents are wired up.
- `DebateOrchestrator` (plan 4-002) depends on this class and is not yet implemented.

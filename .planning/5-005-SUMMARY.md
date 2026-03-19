---
id: 5-005
phase: 5
title: VanguardPipelineRunner and specialist_prompt param
status: complete
commit: 002690c
---

## What Was Done

### forge_agent/core/pipeline.py (modified)

- Added `specialist_prompt: str | None = None` as the seventh parameter to `PipelineRunner.__init__()`.
- Stores it as `self._specialist_prompt`, falling back to `ME_SYSTEM_PROMPT` when `None` — fully backward-compatible.
- Replaced both `system=ME_SYSTEM_PROMPT` in `_run_phase_specialist()` (router path and direct Anthropic path) with `system=self._specialist_prompt`.
- Updated docstring and "All N parameters stored" comment to reflect seven parameters.

### forge_agent/core/vanguard_pipeline.py (created)

- `VanguardPipelineRunner` accepts a `domain` string and routes to the correct specialist `SYSTEM_PROMPT` and `AntagonistClass` via `_DOMAIN_MAP`.
- Valid domains: `"synthmuscle"`, `"mujoco_sim"`, `"cmaes_opt"`, `"actuator_safety"` (enforced by `_VALID_DOMAINS` frozenset).
- Invalid domain → `ValueError` with message listing valid options.
- Constructs `DebateOrchestrator(specialist=None, antagonist=<domain antagonist>)` and passes it to `PipelineRunner` alongside the domain's `specialist_prompt`.
- Exposes `run(request: TaskRequest) -> TaskResult` delegating to `PipelineRunner.run()`.

### forge_agent/tests/test_vanguard_pipeline.py (created)

Nine tests covering all acceptance criteria:

| Test | AC |
|---|---|
| `test_pipeline_stores_custom_specialist_prompt` | AC2 |
| `test_pipeline_uses_me_prompt_by_default` | AC3 |
| `test_vanguard_synthmuscle_runs` | AC4 |
| `test_vanguard_mujoco_sim_runs` | AC5 |
| `test_vanguard_cmaes_opt_runs` | AC6 |
| `test_vanguard_actuator_safety_runs` | AC7 |
| `test_unknown_domain_raises` | AC8 |
| `test_unknown_domain_error_lists_valid_domains` | AC8 (supplemental) |
| `test_vanguard_pipeline_has_debate_verdict` | AC9 |

## Verification

```
ruff check forge_agent/core/pipeline.py forge_agent/core/vanguard_pipeline.py forge_agent/tests/test_vanguard_pipeline.py --ignore E501
# → All checks passed!

pytest forge_agent/tests/test_vanguard_pipeline.py -v --tb=short
# → 9 passed in 0.04s

pytest --tb=short -q
# → 478 passed in 4.22s
```

## P-Guard Compliance

- P1: All method calls verified against actual class definitions.
- P2: All parameters stored or forwarded — none silently ignored. `domain` stored as `self._domain`, `specialist=None` stored in `DebateOrchestrator._specialist`.
- P10/P11: No new packages created.

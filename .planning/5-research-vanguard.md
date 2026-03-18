# Phase 5 Research — Void Vanguard Agents + Pipeline Integration

Date: 2026-03-18

## Scope

Phase 4 scope included "Vanguard pipeline" but this was not implemented. Phase 5
delivers the Void Vanguard Python agent layer and pipeline integration.

## Existing Infrastructure (confirmed by codebase search)

### CLI Handlers (forge_agent/core/cli_dispatcher.py)

All three Vanguard tool handlers are already registered:
- `synthmuscle_fit` (line 512) — Chou-Hannaford PAM parameter fitting via scipy.optimize
- `mujoco_step` (line 608) — deterministic MuJoCo trajectory rollout
- `cmaes_optimize` (line 701) — diagonal CMA-ES with Monte Carlo CVaR gating

### Agent Cards (forge-agents/registry/agent_cards/)

All 8 Vanguard agents have YAML cards:
- synthmuscle_specialist / synthmuscle_antagonist
- mujoco_simulation_specialist / mujoco_simulation_antagonist
- cmaes_optimization_specialist / cmaes_optimization_antagonist
- actuator_safety_specialist / actuator_safety_antagonist

### SKILL.md Files (forge-agents/<agent-id>/SKILL.md)

SKILL.md files confirmed present for:
- synthmuscle_specialist, synthmuscle_antagonist
- mujoco_simulation_specialist
- cmaes_optimization_specialist
- actuator_safety_specialist

### Python Infrastructure (already built in Phases 1-4)

- `AntagonistAgent` ABC: `forge_agent/agents/antagonist_base.py` (4-001)
- `DebateOrchestrator`: `forge_agent/core/debate_orchestrator.py` (4-002)
- `PipelineRunner`: `forge_agent/core/pipeline.py` — hardcodes `ME_SYSTEM_PROMPT`

### Gap: Hardcoded specialist prompt

`PipelineRunner._run_phase_specialist()` hardcodes `ME_SYSTEM_PROMPT` from
`mechanical_engineer.py`. For Vanguard domains, we need domain-specific prompts.

**Solution:** Add `specialist_prompt: str | None = None` parameter to
`PipelineRunner.__init__()`. When None → fall back to ME_SYSTEM_PROMPT (backward
compatible). Vanguard agents can inject their domain prompt.

## Domain Analysis

### Domain 1: Synthmuscle (McKibben PAM)

**CLI tool output keys:** L0_m, D0_m, alpha0_deg, rmse_N, rmse_pct, r2, aic, bic,
  F_max_N, provenance

**Specialist prompt needs:** Chou-Hannaford model, PAM physics, parameter fitting,
  force-length-pressure relationship, pressure dynamics

**Antagonist heuristics:**
1. If `rmse_pct` > 5.0 → `fatal` (RMSE exceeds acceptance threshold)
2. If `r2` < 0.95 → `warning` (insufficient R²)
3. If `aic` or `bic` absent → `warning` (no model selection criteria)
4. Default → `info` (hysteresis not characterized)

### Domain 2: MuJoCo Simulation

**CLI tool output keys:** steps, sim_time_s, seed, mjcf_sha256, joint_pos, joint_vel,
  contact_forces, trajectory_file, provenance

**Antagonist heuristics:**
1. If `seed` absent → `fatal` (non-deterministic simulation)
2. If `steps` < 100 → `warning` (insufficient simulation duration)
3. If `trajectory_file` absent → `warning` (no trajectory recorded)
4. Default → `info` (sim-to-real gap not quantified)

### Domain 3: CMA-ES Optimization

**CLI tool output keys:** best_params, best_fitness, cvar_005, cvar_pass,
  generations, sigma_final, sigma0, lambda_pop, stagnation, convergence_curve

**Antagonist heuristics:**
1. If `cvar_pass` is False → `fatal` (CVaR gate failed)
2. If `stagnation` is True → `warning` (CMA-ES stagnated)
3. If `convergence_curve` absent → `warning` (no convergence evidence)
4. Default → `info`

### Domain 4: Actuator Safety

**Expected output keys:** max_pressure_kPa, burst_pressure_kPa, safety_factor,
  failure_modes, pressure_rating_standard

**Antagonist heuristics:**
1. If `safety_factor` absent or < 2.0 → `fatal`
2. If `burst_pressure_kPa` absent → `warning`
3. If `failure_modes` absent or empty → `warning`
4. Default → `info`

## Pattern for Specialist Agents (from mechanical_engineer.py)

```python
ROLE = "synthmuscle_specialist"
MODEL = "claude-opus-4-6"
TEMPERATURE = 0.2

SYSTEM_PROMPT = f"""..."""
```

No class needed — just constants that PipelineRunner imports.

## Pattern for Antagonist Agents (from antagonist_base.py)

```python
class SynthmuscleAntagonist(AntagonistAgent):
    def __init__(self) -> None:
        super().__init__(agent_id="synthmuscle_antagonist", domain="synthmuscle")

    def _generate_critique(self, specialist_output: dict, context: dict) -> dict:
        # Both params consumed (P2)
        # Heuristic checks on specialist_output fields
        ...
```

## VanguardPipelineRunner Design

`forge_agent/core/vanguard_pipeline.py`:

```python
_VANGUARD_DOMAINS = {
    "synthmuscle": (synthmuscle.SYSTEM_PROMPT, SynthmuscleAntagonist),
    "mujoco_sim": (mujoco_simulation.SYSTEM_PROMPT, MuJoCoSimulationAntagonist),
    "cmaes_opt": (cmaes_optimization.SYSTEM_PROMPT, CMAESOptimizationAntagonist),
    "actuator_safety": (actuator_safety.SYSTEM_PROMPT, ActuatorSafetyAntagonist),
}

class VanguardPipelineRunner:
    def __init__(self, domain: str, config: dict, ...) -> None:
        prompt, AntagonistClass = _VANGUARD_DOMAINS[domain]
        antagonist = AntagonistClass()
        # NullSpecialist — VanguardPipelineRunner doesn't have a specialist object
        # DebateOrchestrator needs specialist arg (P2 stored for future use)
        debate_orchestrator = DebateOrchestrator(
            specialist=None,  # stored but not called in current impl
            antagonist=antagonist,
        )
        self._runner = PipelineRunner(
            config=config,
            specialist_prompt=prompt,
            debate_orchestrator=debate_orchestrator,
            ...
        )

    def run(self, request: TaskRequest) -> TaskResult:
        return self._runner.run(request)
```

## P-Guard Checklist (applies across all plans)

| Guard | Risk | Mitigation |
|---|---|---|
| P1 — interface mismatch | Medium | Verify AntagonistAgent.critique() signature before subclassing. Verify PipelineRunner.__init__ signature before adding specialist_prompt param. |
| P2 — silently ignored params | High | Both specialist_output and context consumed in _generate_critique. specialist param in DebateOrchestrator stored (not dropped). |
| P7 — error codes | Low | Antagonists set error_code=None (base class permits None per design). |
| P10/P11 — pyproject.toml | No | No new sub-packages. |

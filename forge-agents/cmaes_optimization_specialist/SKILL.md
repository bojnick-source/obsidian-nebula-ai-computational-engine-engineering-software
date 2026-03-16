# CMA-ES Optimization Specialist — SKILL Definition

**Agent ID:** `cmaes_optimization_specialist`
**Domain:** Diagonal CMA-ES Evolutionary Optimisation — Population, Covariance Adaptation, Monte Carlo Gating
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The CMA-ES Optimization Specialist runs Diagonal Covariance Matrix Adaptation Evolution
Strategy (dCMA-ES) optimisation over PAM control parameters within the Void Vanguard project.
It configures population size, step size, constraint handling, and Monte Carlo (MC) CVaR gating
to produce robust, hardware-safe optima.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Diagonal CMA-ES configuration | Active (MVP) | dCMA-ES; full CMA optional at high n |
| Population size selection | Active (MVP) | λ ≥ 4 + 3·ln(n) rule enforced |
| Step size initialisation | Active (MVP) | σ₀ = 1/3 of parameter range |
| Monte Carlo CVaR gating | Active (Level 2) | N ≥ 400, α = 0.05 |
| Constraint feasibility enforcement | Active (Level 2) | Pressure bounds, contraction limits |
| Multi-objective Pareto (performance/safety) | Planned (V1) | Level 3 |
| Warm-start from previous run | Planned (V2) | Level 4 |
| Full CMA-ES (non-diagonal) | Planned (V3) | Level 5, n > 20 parameters |

### Algorithm: Diagonal CMA-ES

Diagonal CMA-ES adapts a diagonal covariance matrix C = diag(c₁, ..., cₙ):

```
x_k^(i) ~ N(m_k, σ_k² · C_k)    i = 1..λ
m_{k+1} = Σᵢ wᵢ · x_k^(i:λ)      (weighted mean of top-μ)
σ_{k+1} = σ_k · exp(cσ/dσ · (‖pσ‖/χₙ - 1))
```

Population and selection parameters:
- `λ = 4 + floor(3·ln(n))` (minimum population size — NEVER reduce below this)
- `μ = floor(λ/2)` (number of parents)
- `wᵢ = ln(μ + 0.5) - ln(i)` / Σ (recombination weights)
- `cσ = (μ_w + 2) / (n + μ_w + 5)` (step-size control learning rate)
- `dσ = 1 + 2·max(0, √((μ_w-1)/(n+1)) - 1) + cσ`

### Parameter Space Table (Void Vanguard)

| Parameter | Symbol | Range | Units | Notes |
|---|---|---|---|---|
| PAM activation trajectory amplitude | A | [0, 1] | — | Per-actuator, per phase |
| Activation rise time | τ_r | [0.005, 0.05] | s | ≥ PAM timeconst activation |
| Activation hold duration | τ_h | [0.01, 0.5] | s | Task-dependent |
| Activation fall time | τ_f | [0.005, 0.1] | s | ≥ PAM timeconst deactivation |
| Inter-actuator phase offset | φ | [-π, π] | rad | Synergy coordination |

### Monte Carlo CVaR Gating

Before accepting a candidate optimum, evaluate robustness under DR:

```
CVaR_{α}(X) = E[loss | loss > VaR_α(X)]
```

- α = 0.05 (5th percentile — worst-case 5% of DR scenarios)
- N_MC ≥ 400 samples per candidate evaluation (required for α=0.05 stability)
- Gate threshold: `CVaR_0.05(tracking_error) < 8°` joint angle
- Candidates failing CVaR gate are penalised (constraint handling: augmented Lagrangian)

### Tools Allowed

```yaml
tools_allowed:
  - cmaes_optimize   # CLI: run dCMA-ES optimisation with MC gating
  - mujoco_step      # CLI: trajectory rollout for fitness evaluation
  - numpy_scipy      # statistics, CVaR computation
```

### Mandatory Output Fields

Every CMA-ES Optimization Specialist output MUST include:
1. `findings` — list of specific numerical results with units
2. `assumptions` — NEVER null; minimum three domain-specific assumptions
3. `what_would_falsify` — specific condition that invalidates the optimum
4. `provenance` — tool version + config SHA256 + seed
5. `confidence` — float 0.0–1.0
6. `optim_summary` — structured optimisation summary (see Output Contract)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Best fitness: X.XX deg RMS (tracking error) after XXX generations"
  - "CVaR_0.05 of best candidate: X.XX deg (threshold: 8.0 deg)"
  - "Population λ=XX (n=X parameters, minimum λ_min=XX)"
  - "Convergence: σ_k = X.XX (σ_0 = X.XX), ratio = X.XX"
assumptions:
  - "Fitness evaluated on MuJoCo simulator — sim-to-real gap not eliminated"
  - "DR ranges cover manufacturing batch variation only — wear not modelled"
  - "Diagonal CMA-ES valid — parameters assumed approximately decorrelated"
what_would_falsify: >
  Hardware tracking error > 2× CVaR_0.05 simulation estimate;
  or σ_k fails to decrease monotonically over last 100 generations (stagnation).
provenance: "cma 3.3.0 — config SHA256: [hash] — seed: 42"
confidence: 0.80
optim_summary:
  algorithm: "dCMA-ES"
  n_params: 0
  lambda_pop: 0
  lambda_min: 0
  generations: 0
  best_fitness: 0.0
  cvar_005: 0.0
  cvar_threshold: 8.0
  cvar_gate: "FAIL"
  sigma_final: 0.0
  status: "unverified"
```

---

## Escalation Flags

Raise **[FULL CMA-ES REQUIRED]** when:
- `n > 20` parameters and parameter correlations suspected (diagonal assumption violated)
- CVaR gate fails after 500 generations — parameter space likely non-convex, escalate to CMA-ES with restart

Raise **[SIM-TO-REAL VALIDATION REQUIRED]** when:
- Best candidate CVaR_0.05 < gate threshold but hardware deviates > 2× prediction

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | dCMA-ES configuration, population sizing, σ₀ selection |
| 2 | Apprentice | 0.40–0.59 | MC CVaR gating, constraint feasibility |
| 3 | Journeyman | 0.60–0.74 | Multi-objective Pareto, warm-start |
| 4 | Expert | 0.75–0.89 | Adaptive DR during optimisation |
| 5 | Master | 0.90–1.00 | Full CMA-ES with restart, certification pipeline |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Undersized population**: λ < 4+3·ln(n) — CMA-ES cannot adapt covariance reliably; premature convergence guaranteed
- **σ₀ too small**: σ₀ < 1/10 of parameter range — algorithm starts over-exploiting, never explores; increase σ₀ to 1/3 of range
- **CVaR N too small**: N < 400 for α=0.05 — CVaR estimate has ±30% error; gate is meaningless
- **No constraint feasibility**: ignoring pressure bounds during optimisation — hardware damage risk; use augmented Lagrangian from generation 1
- **Stagnation not detected**: σ_k not monitored — silent premature convergence; add stagnation detection (σ_k < 1e-6·σ₀ → restart)

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft optimisation methods — dCMA-ES equations, CVaR formulation, MC protocol |
| 4 | Peer review of CMA-ES convergence claims |
| 5 | Full certification panel — optimum safety and sim-to-real robustness |

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current defaults.

Quick reference:
- Default algorithm: dCMA-ES (upgrade to full CMA-ES only if n > 20)
- Population: `λ = 4 + floor(3·ln(n))`, never reduce
- σ₀: 1/3 of parameter range for each dimension
- CVaR N: 500 (minimum 400)
- CVaR α: 0.05 (5th percentile)
- CVaR gate: 8° joint angle RMS

---

## References

- Hansen, N. (2016). The CMA evolution strategy: A tutorial. *arXiv:1604.00772*.
- Rockafellar, R.T. & Uryasev, S. (2000). Optimization of conditional value-at-risk. *J. Risk*, 2(3), 21–41.
- Uchibe, E. (2021). Model-free deep reinforcement learning with multi-task DR. *IEEE RA-L*.
- `cma` Python package (Hansen) — dCMA-ES reference implementation

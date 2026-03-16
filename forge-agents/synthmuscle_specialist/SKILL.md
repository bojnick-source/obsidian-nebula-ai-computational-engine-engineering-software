# Synthmuscle Specialist — SKILL Definition

**Agent ID:** `synthmuscle_specialist`
**Domain:** Synthetic Muscle Actuator Modelling — McKibben PAM Physics, Parameter Fitting, Pressure Dynamics
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Synthmuscle Specialist models McKibben pneumatic artificial muscles (PAMs) as used
in the Void Vanguard project. It produces force-length-pressure characterisations,
fits model parameters to measured data, and validates pressure dynamics against
target trajectories.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Force-length-pressure model (analytical) | Active (MVP) | Chou–Hannaford model |
| Geometric contraction ratio analysis | Active (MVP) | α, L, D relationships |
| Parameter fitting to empirical data | Active (Level 2) | Least-squares / scipy.optimize |
| Pressure dynamics modelling | Planned (V1) | First-order valve model |
| Fatigue and hysteresis characterisation | Planned (V1) | Level 3 |
| Multi-PAM synergistic analysis | Planned (V2) | Level 4 |
| Full-chain force trajectory optimisation | Planned (V3) | Level 5 Master |

### McKibben PAM Physics

The canonical Chou–Hannaford force model:

```
F(L, P) = (π D₀²/4) · P · [3(L/L₀)² cos²α₀ - 1] / tan²α₀
```

Variables:
- `F` — axial force [N]
- `L` — current length [m]; `L₀` — rest length [m]
- `D₀` — rest outer diameter [m]
- `P` — gauge pressure [Pa]
- `α₀` — braid angle at rest [rad] (typically 20°–30°)

Contraction ratio: `ε = (L₀ - L) / L₀` (range 0–0.25 typical)

Geometric constraint: `cos α = L / (n · b)` where `n` = number of turns, `b` = braid strand length.

### Parameter Fitting Metrics

| Metric | Acceptance Threshold |
|---|---|
| RMSE (force) | < 2% of F_max |
| MAE (force) | < 1.5% of F_max |
| R² | ≥ 0.98 |
| AIC (model selection) | Lower is better; compare vs polynomial baseline |
| BIC (model selection) | Lower is better; penalises excess parameters |

### Tools Allowed

```yaml
tools_allowed:
  - numpy_scipy    # parameter fitting, optimisation
  - sympy          # symbolic force model derivation
  - synthmuscle_fit  # CLI: fit PAM parameters to measured data
```

### Mandatory Output Fields

Every Synthmuscle Specialist output MUST include:
1. `findings` — list of specific numerical results with units
2. `assumptions` — NEVER null; minimum three domain-specific assumptions
3. `what_would_falsify` — specific condition that invalidates the analysis
4. `provenance` — tool version + input hash
5. `confidence` — float 0.0–1.0
6. `pam_summary` — structured PAM characterisation (see Output Contract)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "F_max: X.XX [N] at P=XXX kPa, ε=0 (analytical, Chou-Hannaford)"
  - "Contraction at P=XXX kPa, load=XX N: ε = X.XX"
  - "Fit quality: RMSE=X.XX N (X.XX% F_max), R²=0.XXX"
assumptions:
  - "Braid inextensible — no fibre elastic stretch"
  - "Bladder mass negligible — quasi-static force balance"
  - "Pressure uniform along actuator length — no pressure drop"
what_would_falsify: >
  Measured F deviates > 5% from model at P > 200 kPa or ε > 0.20;
  or R² < 0.98 on held-out validation set from the same actuator batch.
provenance: "scipy 1.11.0 — input SHA256: [hash]"
confidence: 0.80
pam_summary:
  model: "Chou-Hannaford"
  L0_m: 0.0
  D0_m: 0.0
  alpha0_deg: 0.0
  P_max_kPa: 0.0
  F_max_N: 0.0
  fit_rmse_pct: 0.0
  fit_r2: 0.0
  status: "unverified"
```

---

## Escalation Flags

Raise **[PAM SIMULATION REQUIRED]** when:
- Operating pressure exceeds 400 kPa (braid inextensibility assumption violated)
- Contraction ratio ε > 0.25 (geometric model breaks down)
- Hysteresis loop area > 8% of total force envelope (dynamic effects dominate)
- Multi-PAM antagonistic pair required (coupling not captured by single-muscle model)

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Force-length-pressure model, geometric analysis |
| 2 | Apprentice | 0.40–0.59 | Parameter fitting, RMSE/R² reporting |
| 3 | Journeyman | 0.60–0.74 | Pressure dynamics, hysteresis modelling |
| 4 | Expert | 0.75–0.89 | Fatigue characterisation, multi-PAM synergy |
| 5 | Master | 0.90–1.00 | Full-chain force trajectory optimisation |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Braid extensibility ignored**: using Chou–Hannaford without checking fibre stretch — introduces > 15% force error above 350 kPa
- **Gauge vs absolute pressure**: using absolute pressure in the model instead of gauge — shifts F(P) by atmospheric offset (~101 kPa), invalidating low-pressure regime
- **Missing hysteresis flag**: reporting a single force value without noting that loading and unloading paths differ by up to 10%
- **Rest-length measurement error**: L₀ measured under load instead of zero-load — corrupts ε and all downstream force predictions
- **Overfit parameter set**: fitting α₀, L₀, D₀ simultaneously to sparse data — AIC/BIC must be computed vs. simpler models to justify added parameters

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods section — PAM model derivation, nomenclature per IEEE RA-L style |
| 4 | Peer review of `synthmuscle_antagonist` critique — rate objections minor/major/fatal |
| 5 | Full academic panel assessment — multi-output PAM characterisation synthesis |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  subsection_title: "McKibben PAM Force Model"
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "synthmuscle_antagonist"
  target_run_id: "..."
  decision: "major_revision"
  objections: []
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current defaults.

Quick reference:
- Default model: Chou–Hannaford (escalate to extended model only when R² < 0.95)
- Optimiser: `scipy.optimize.least_squares` with `method='trf'`, `loss='soft_l1'`
- Confidence threshold for release: 0.75
- Always report both RMSE and R²; flag if R² < 0.98

---

## References

- Chou, C.-P. & Hannaford, B. (1996). Measurement and modeling of McKibben pneumatic artificial muscles. *IEEE TRA*, 12(1), 90–102.
- Tondu, B. & Lopez, P. (2000). Modeling and control of McKibben artificial muscle robot actuators. *IEEE Control Systems*, 20(2), 15–38.
- Festo AG — DMSP/MAS series datasheet (braid geometry validation values)

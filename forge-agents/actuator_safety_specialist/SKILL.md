# Actuator Safety Specialist — SKILL Definition

**Agent ID:** `actuator_safety_specialist`
**Domain:** Actuator Safety Layer — QP Safety Filter, State Machine (NOMINAL/CLAMPING/KILLED), Thermal Derating
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Actuator Safety Specialist designs and validates the safety layer for McKibben PAM
actuators in the Void Vanguard project. It implements the QP safety filter, maintains the
three-state machine (NOMINAL → CLAMPING → KILLED), and computes thermal derating curves
to prevent actuator damage under sustained high-pressure operation.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Safety state machine design | Active (MVP) | NOMINAL/CLAMPING/KILLED with KILLED latch |
| QP safety filter formulation | Active (MVP) | CBF-based QP with pressure bounds |
| Thermal derating computation | Active (Level 2) | Temperature-dependent F_max reduction |
| Fault propagation analysis | Active (Level 2) | Sensor fault → state transition mapping |
| Pressure relief valve sizing | Planned (V1) | Level 3 |
| Hardware-in-loop safety validation | Planned (V2) | Level 4 |
| Formal safety verification (dReal/Flow*) | Planned (V3) | Level 5 Master |

### Safety State Machine

```
NOMINAL ──[P > P_clamp OR T > T_clamp]──► CLAMPING
   ▲                                           │
   │ [P < P_resume AND T < T_resume]            │
   └─────────────────────────────────────────────┘
                                                │
CLAMPING ──[P > P_kill OR T > T_kill OR         │
            sensor_fault = TRUE]────────► KILLED │
                                           (LATCH — no auto-recovery)
```

State thresholds (nominal values — tunable per actuator batch):

| Threshold | Symbol | Default | Units |
|---|---|---|---|
| Clamping pressure entry | P_clamp | 380 kPa | kPa gauge |
| Clamping temp entry | T_clamp | 65 °C | °C |
| Clamping pressure resume | P_resume | 340 kPa | kPa gauge |
| Clamping temp resume | T_resume | 55 °C | °C |
| Kill pressure | P_kill | 420 kPa | kPa gauge |
| Kill temperature | T_kill | 80 °C | °C |

**KILLED is a latch**: once entered, requires explicit hardware reset (operator intervention).
Software reset alone MUST NOT clear KILLED state.

### QP Safety Filter Formulation

The safety filter solves at each control step (10 ms):

```
min_{u_safe}  ‖u_safe - u_nom‖²
subject to:
  ∇h(x)ᵀ f(x, u_safe) + α·h(x) ≥ 0    (CBF condition)
  u_min ≤ u_safe ≤ u_max               (actuator bounds)
  P(u_safe) ≤ P_clamp                  (pressure safety)
```

Where:
- `h(x) = P_max - P(x)` — Control Barrier Function (pressure headroom)
- `α` — CBF decay rate, typically 10 s⁻¹
- `u_nom` — nominal CMA-ES commanded activation
- `u_safe` — safe activation output to actuator

**QP solve time requirement**: must complete in < 5 ms on target hardware (to maintain 10 ms loop).
Use `osqp` (warm-started) or `qpOASES` for real-time compliance.

### Thermal Derating Curve

Force capacity derates with temperature:

```
F_max(T) = F_max_nominal · (1 - k_T · max(0, T - T_nominal))
```

Parameters:
- `T_nominal` = 20 °C (calibration temperature)
- `k_T` = 0.008 °C⁻¹ (derating coefficient — 0.8% per °C above nominal)
- `T_clamp` = 65 °C → F_max(65) = F_max_nominal · (1 - 0.008·45) = 0.64 · F_max_nominal
- `T_kill` = 80 °C → F_max(80) = F_max_nominal · 0.52 (52% of nominal)

### Tools Allowed

```yaml
tools_allowed:
  - numpy_scipy    # QP setup, thermal computation
  - osqp           # QP solver (real-time, warm-start)
```

### Mandatory Output Fields

Every Actuator Safety Specialist output MUST include:
1. `findings` — list of specific numerical results with units
2. `assumptions` — NEVER null; minimum three domain-specific assumptions
3. `what_would_falsify` — specific condition that invalidates the safety analysis
4. `provenance` — solver version + config SHA256
5. `confidence` — float 0.0–1.0
6. `safety_summary` — structured safety assessment (see Output Contract)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "QP solve time: X.XX ms (threshold: 5.0 ms) — PASS/FAIL"
  - "F_max at T_clamp=65°C: X.XX N (X.XX% of nominal)"
  - "KILLED state: latch verified — no software-only reset path"
  - "Fault coverage: X/Y fault modes mapped to state transitions"
assumptions:
  - "Pressure sensor accuracy ±5 kPa — sensor fault defined as |P_read - P_model| > 20 kPa"
  - "CBF decay rate α=10 s⁻¹ — conservative for PAM pressure rise rate < 50 kPa/s"
  - "Thermal model first-order with k_T=0.008 °C⁻¹ — valid for neoprene bladder below 80°C"
what_would_falsify: >
  QP solve time > 5 ms on target hardware under worst-case constraint set;
  or KILLED state cleared by software reset without hardware interlock.
provenance: "osqp 0.6.3 — config SHA256: [hash]"
confidence: 0.85
safety_summary:
  state_machine: "NOMINAL/CLAMPING/KILLED"
  killed_latch: true
  killed_software_reset: false
  qp_solver: "osqp"
  qp_max_ms: 0.0
  qp_threshold_ms: 5.0
  qp_pass: false
  T_clamp: 65.0
  F_max_at_T_clamp_pct: 0.0
  fault_modes_covered: 0
  fault_modes_total: 0
  status: "unverified"
```

---

## Escalation Flags

Raise **[HARDWARE SAFETY REVIEW REQUIRED]** when:
- QP solve time > 5 ms on target hardware — control loop timing violated
- KILLED reset path exists in software — must be hardware-only
- Sensor fault detection latency > 20 ms — unsafe gap between fault and state transition
- Thermal model deviates > 15% from measured F_max(T) curve

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | State machine, QP formulation, thermal derating |
| 2 | Apprentice | 0.40–0.59 | Fault propagation analysis, sensor fault detection |
| 3 | Journeyman | 0.60–0.74 | Pressure relief sizing, hardware-in-loop |
| 4 | Expert | 0.75–0.89 | Multi-actuator safety coordination |
| 5 | Master | 0.90–1.00 | Formal safety verification (dReal/Flow*) |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Software KILLED reset**: implementing KILLED reset in software without hardware interlock — single software failure defeats the safety layer entirely
- **QP warm-start disabled**: running cold-start QP every cycle — solve time 3–5× higher, loop violation likely
- **CBF α too large**: α > 50 s⁻¹ with slow pressure dynamics → filter too aggressive, excessive intervention → actuator oscillation
- **Thermal model extrapolation**: using k_T above T_kill — bladder chemistry changes; model invalid; use KILLED threshold
- **Fault detection hysteresis gap**: P_kill set equal to P_clamp → no hysteresis → chattering between CLAMPING and KILLED

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft safety architecture section — CBF QP formulation, state machine diagram |
| 4 | Peer review of safety claim — rate fault coverage and QP timing adequacy |
| 5 | Formal safety panel — full dReal/Flow* verification synthesis |

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current defaults.

Quick reference:
- Default QP solver: osqp (warm-start enabled)
- QP solve time threshold: 5 ms
- CBF α default: 10 s⁻¹ (increase only with pressure rate justification)
- Thermal derating k_T: 0.008 °C⁻¹ (neoprene bladder; verify per batch)
- Confidence threshold for hardware deployment: 0.90

---

## References

- Ames, A.D. et al. (2019). Control barrier functions: Theory and applications. *ECC 2019*.
- Stellato, B. et al. (2020). OSQP: An operator splitting solver for quadratic programs. *Math. Prog. Comp.*, 12, 637–672.
- IEC 61508 — Functional Safety of Electrical/Electronic/Programmable Electronic Safety-related Systems
- ISO 10218 — Safety requirements for industrial robots (state machine reference)

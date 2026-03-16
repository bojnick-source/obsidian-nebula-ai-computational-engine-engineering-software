---
title: "Void Vanguard Safety Architecture"
project: void-vanguard
domain: actuator_safety
tags: [safety, qp-filter, cbf, state-machine, thermal, iec61508]
created: 2026-03-16
---

# Void Vanguard Safety Architecture

## Safety State Machine

```
NOMINAL ──[P > P_clamp OR T > T_clamp]──► CLAMPING
   ▲                                           │
   │ [P < P_resume AND T < T_resume]            │
   └─────────────────────────────────────────────┘
                                                │
CLAMPING ──[P > P_kill OR T > T_kill OR         │
            sensor_fault = TRUE]────────► KILLED │
                                           (LATCH)
```

KILLED state requires **hardware interlock reset** — no software-only clear path.

### Thresholds

| Threshold | Default | Units |
|---|---|---|
| P_clamp | 380 kPa | gauge |
| P_resume | 340 kPa | gauge |
| P_kill | 420 kPa | gauge |
| T_clamp | 65 °C | |
| T_resume | 55 °C | |
| T_kill | 80 °C | |

## QP Safety Filter

Solves at 100 Hz (10 ms loop):

$$
\min_{u_{safe}} \|u_{safe} - u_{nom}\|^2
\quad \text{s.t.} \quad
\nabla h(x)^\top f(x, u_{safe}) + \alpha h(x) \geq 0, \quad
u_{min} \leq u_{safe} \leq u_{max}
$$

- **CBF**: h(x) = P_max − P(x) (pressure headroom)
- **α** = 10 s⁻¹ (CBF decay rate)
- **Solver**: OSQP with warm-start (solve time < 5 ms)
- **Control loop**: 100 Hz; QP budget = 5 ms/step

## Thermal Derating

$$F_{max}(T) = F_{max,nominal} \cdot \left(1 - k_T \cdot \max(0, T - T_{nominal})\right)$$

- k_T = 0.008 °C⁻¹ (neoprene bladder)
- T_nominal = 20 °C
- At T_clamp = 65°C: F_max = 64% of nominal
- Model valid below T_kill = 80°C only

## Fault Coverage Requirements

Minimum 80% of identified fault modes must be mapped to state transitions.
Uncovered faults escalate to `actuator_safety_antagonist` review.

Common fault modes:
1. Pressure sensor open-circuit → P_read = 0 → sensor_fault = TRUE → KILLED
2. Pressure sensor short-circuit → P_read = MAX → P > P_kill → KILLED
3. Temperature sensor failure → T_read = NaN → sensor_fault = TRUE → KILLED
4. Valve stuck open → P rising uncontrolled → P > P_kill → KILLED
5. CBF infeasible (QP no solution) → de-activate all actuators → KILLED

## Key Rules

1. KILLED latch: hardware reset only — no software path clears it
2. QP warm-start must be enabled; cold-start QP exceeds 5 ms budget
3. CBF α must be justified by pressure rise rate (≤ 50 kPa/s → α=10 is safe)
4. P_resume < P_clamp - 10 kPa (hysteresis gap to prevent chattering)
5. Thermal model must not be extrapolated above T_kill

## References

- Ames, A.D. et al. (2019). Control barrier functions. *ECC 2019*.
- Stellato, B. et al. (2020). OSQP. *Math. Prog. Comp.*, 12, 637–672.
- IEC 61508 — Functional Safety of E/E/PE Safety-related Systems.

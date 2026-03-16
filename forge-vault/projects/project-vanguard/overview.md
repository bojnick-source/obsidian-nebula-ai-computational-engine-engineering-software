---
title: "Void Vanguard — Project Overview"
project: void-vanguard
source_repo: bojnick-source/DARPA-lift
status: active
tags: [vanguard, pam, mujoco, cmaes, safety, typescript]
created: 2026-03-16
---

# Void Vanguard — Project Overview

> **Note:** The source repository is named `DARPA-lift` for operational reasons.
> The canonical project name inside FORGE is **Void Vanguard**.

## Project Summary

Void Vanguard is a compliant-actuator robotics project centred on McKibben pneumatic
artificial muscles (PAMs). The engineering pipeline runs from physics characterisation
through simulation-based optimisation to a safety-gated hardware deployment, with a
TypeScript/React collaborative design UI layer (Yjs CRDT sync, audit trail, XR workspace).

## Architecture

```
synthmuscle_specialist
    │  F(L,P) characterisation → pam_summary
    ▼
mujoco_simulation_specialist
    │  MJCF model + DR rollouts → sim_summary
    ▼
cmaes_optimization_specialist
    │  dCMA-ES + CVaR gating → optim_summary
    ▼
actuator_safety_specialist
    │  QP filter + state machine → safety_summary
    ▼
Hardware deployment (PAM rig)
    │
    └── Void Vanguard UI (TypeScript / Yjs CRDT)
```

## Domains

| Domain | Specialist | Antagonist |
|---|---|---|
| McKibben PAM physics | `synthmuscle_specialist` | `synthmuscle_antagonist` |
| MuJoCo simulation | `mujoco_simulation_specialist` | `mujoco_simulation_antagonist` |
| Diagonal CMA-ES | `cmaes_optimization_specialist` | `cmaes_optimization_antagonist` |
| Actuator safety | `actuator_safety_specialist` | `actuator_safety_antagonist` |

## Key Physical Parameters

- Actuator family: McKibben PAM (neoprene bladder, polyester braid)
- Operating pressure: 0–400 kPa gauge
- Max contraction: ε ≤ 0.25
- Braid angle (rest): α₀ ≈ 20°–30°
- Force model: Chou–Hannaford (1996)

## CLI Tools

| Tool | Handler | Purpose |
|---|---|---|
| `synthmuscle_fit` | `cli_dispatcher._synthmuscle_fit` | Fit PAM Chou–Hannaford model to data |
| `mujoco_step` | `cli_dispatcher._mujoco_step` | Deterministic MuJoCo trajectory rollout |
| `cmaes_optimize` | `cli_dispatcher._cmaes_optimize` | dCMA-ES with MC CVaR gating |

## Related Notes

- [[mckibben-pam-reference]] — Physics equations, parameter table
- [[safety-architecture]] — QP filter, state machine, thermal derating
- [[optimisation-strategy]] — dCMA-ES algorithm, population sizing, CVaR gating

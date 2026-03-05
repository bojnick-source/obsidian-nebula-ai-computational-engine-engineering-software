# NVIDIA Physics Stack — R&D Lane

> R&D evaluation of NVIDIA physics tools for FORGE integration.

---

## Tools Under Evaluation

| Tool | Purpose | Notes |
|---|---|---|
| PhysX | Rigid body / articulated dynamics | GPU-accelerated; Omniverse integration |
| Warp | GPU-accelerated simulation kernel | Python API; differentiable physics |
| Newton | Robot learning physics | Isaac Lab integration |
| PhysicsNeMo | Physics-informed ML | Neural operator training |

---

## Potential Integration Points

- Simulation verification: compare FORGE FEA results with PhysX rigid body simulation
- Digital twin (Vanguard): O3DE + PhysX for mechanism verification
- Differentiable simulation: Warp for gradient-based design optimization
- Robot learning: Newton for control system verification (Phoenix actuators)

---

## Evaluation Criteria

1. Does it add capability not achievable with open-source tools?
2. License compatibility with FORGE
3. Integration complexity (MCP wrapper feasibility)
4. Maintenance burden

## Status: R&D — evaluate after V1 toolchain is stable

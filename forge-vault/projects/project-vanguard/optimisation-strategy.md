---
title: "Void Vanguard Optimisation Strategy"
project: void-vanguard
domain: cmaes_optimization
tags: [cmaes, cvar, monte-carlo, optimisation, pam-control]
created: 2026-03-16
---

# Void Vanguard Optimisation Strategy

## Algorithm: Diagonal CMA-ES

Diagonal Covariance Matrix Adaptation Evolution Strategy (dCMA-ES).
Adapts a diagonal covariance matrix C = diag(c₁, ..., cₙ) over generations.

### Key Equations

$$x_k^{(i)} \sim \mathcal{N}(m_k, \sigma_k^2 C_k), \quad i = 1\ldots\lambda$$

$$m_{k+1} = \sum_{i=1}^{\mu} w_i \cdot x_k^{(i:\lambda)}$$

$$\sigma_{k+1} = \sigma_k \exp\!\left(\frac{c_\sigma}{d_\sigma} \left(\frac{\|p_\sigma\|}{\chi_n} - 1\right)\right)$$

### Population Sizing Rule

$$\lambda \geq 4 + \lfloor 3 \ln n \rfloor \quad \text{(MANDATORY — never reduce)}$$

| n (params) | λ_min |
|---|---|
| 5 | 9 |
| 8 | 10 |
| 10 | 11 |
| 15 | 12 |
| 20 | 13 |

### Initial Step Size

$$\sigma_0 = \frac{1}{3} \cdot \text{mean}(\text{param ranges})$$

## PAM Control Parameter Space

| Parameter | Symbol | Range | Notes |
|---|---|---|---|
| Activation amplitude | A | [0, 1] | Per-actuator, per phase |
| Rise time | τ_r | [0.005, 0.05] s | ≥ PAM activation timeconst |
| Hold duration | τ_h | [0.01, 0.5] s | Task-dependent |
| Fall time | τ_f | [0.005, 0.1] s | ≥ PAM deactivation timeconst |
| Phase offset | φ | [-π, π] rad | Inter-actuator coordination |

## Monte Carlo CVaR Gating

Robustness metric evaluated before accepting an optimum:

$$\text{CVaR}_\alpha(X) = \mathbb{E}\left[\text{loss} \mid \text{loss} > \text{VaR}_\alpha(X)\right]$$

### Requirements

| Parameter | Value |
|---|---|
| α | 0.05 (5th percentile worst case) |
| N_MC samples | ≥ 500 (minimum 400) |
| CVaR gate threshold | 8° joint angle RMS |
| DR perturbation | ±5% uniform on all PAM parameters |

### Acceptance Protocol

1. Run dCMA-ES to convergence (or max_generations)
2. Take best_x candidate
3. Evaluate CVaR_0.05 over N_MC DR perturbations
4. Accept if CVaR_0.05 ≤ 8° AND constraints feasible
5. Reject and restart with larger σ₀ if CVaR gate fails after 500 generations

## Stagnation Detection

- Monitor σ_k each generation
- If σ_k < 1e-6 · σ₀ → premature convergence → restart with σ₀ × 2

## Constraint Handling

Augmented Lagrangian from generation 1:
- Pressure bounds: P ≤ P_clamp (380 kPa)
- Contraction bounds: ε ≤ 0.25
- Thermal bounds: T ≤ T_clamp (65°C) under sustained activation

## Pipeline Handoff

```
mujoco_simulation_specialist
    → provides DR rollout function for CMA-ES fitness evaluation
    → DR samples: 500/generation, seed documented

cmaes_optimization_specialist
    → produces best_params dict
    → provides CVaR_0.05 and cvar_pass flag

actuator_safety_specialist
    → validates best_params against safety bounds
    → runs QP filter over optimised trajectory
```

## References

- Hansen, N. (2016). The CMA evolution strategy: A tutorial. *arXiv:1604.00772*.
- Rockafellar, R.T. & Uryasev, S. (2000). Optimization of conditional value-at-risk. *J. Risk*, 2(3), 21–41.
- `cma` Python package (Hansen) — reference dCMA-ES implementation.

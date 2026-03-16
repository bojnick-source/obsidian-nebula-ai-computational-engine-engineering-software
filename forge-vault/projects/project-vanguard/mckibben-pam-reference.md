---
title: "McKibben PAM Reference"
project: void-vanguard
domain: synthmuscle
tags: [pam, mckibben, chou-hannaford, actuator, force-model]
created: 2026-03-16
---

# McKibben PAM Reference

## Chou–Hannaford Force Model

The canonical quasi-static force model (Chou & Hannaford, 1996):

$$
F(L, P) = \frac{\pi D_0^2}{4} \cdot P \cdot \frac{3(L/L_0)^2 \cos^2\alpha_0 - 1}{\tan^2\alpha_0}
$$

### Variables

| Symbol | Name | Units | Notes |
|---|---|---|---|
| F | Axial force | N | Positive = contraction |
| L | Current length | m | |
| L₀ | Rest length | m | Zero-load, zero-pressure |
| D₀ | Rest outer diameter | m | |
| P | Gauge pressure | Pa | NOT absolute |
| α₀ | Braid angle at rest | rad | Typically 20°–30° |
| ε = (L₀−L)/L₀ | Contraction ratio | — | Range 0–0.25 |

### Geometric Constraint

$$\cos\alpha = \frac{L}{n \cdot b}$$

where n = number of braid turns, b = strand length.

## Validity Domain

| Condition | Requirement | Consequence if violated |
|---|---|---|
| Braid inextensibility | P < 350 kPa | F underestimated — extensibility correction needed |
| Quasi-static | dε/dt < 0.5 s⁻¹ | Dynamic pressure drop not captured |
| Geometry | ε ≤ 0.25 | Geometric model breaks down |
| Braid angle | α₀ ≤ 35° | Model derivation assumes small-angle approximation |

## Parameter Fitting Protocol

1. Collect F(L, P) at ≥ 5 pressure levels, ≥ 10 length steps each
2. Fit [L₀, D₀, α₀] via `scipy.optimize.least_squares` with `loss='soft_l1'`
3. Report RMSE (%), R², AIC, BIC
4. Acceptance gate: **R² ≥ 0.98**, **RMSE < 2% F_max**
5. Validate on held-out 20% of data

## Typical Parameter Values (10 mm diameter PAM)

| Parameter | Value | Source |
|---|---|---|
| L₀ | 90–120 mm | Chou (1996) Table II |
| D₀ | 10 mm | Chou (1996) Table II |
| α₀ | 25° | Chou (1996) Table II |
| F_max (P=300 kPa) | ~400 N | Chou (1996) Table II |
| Max contraction ε | 0.22 | Festo DMSP series |

## Hysteresis

PAMs exhibit hysteresis: loading path force > unloading path force by 5–10%.
Single-direction force data must be flagged; two-direction characterisation required
for hardware control accuracy.

## References

- Chou, C.-P. & Hannaford, B. (1996). Measurement and modeling of McKibben pneumatic artificial muscles. *IEEE TRA*, 12(1), 90–102.
- Tondu, B. (2012). Modelling of the McKibben artificial muscle: A review. *J. Intelligent Material Systems and Structures*, 23(3), 225–253.

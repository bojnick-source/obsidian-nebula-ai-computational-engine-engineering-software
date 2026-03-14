# dark-leaf-v2 — Salvaged Solvers

Polyglot solver library salvaged from
[`bojnick-source/DARK_leaf_drone_4-1_V2`](https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2).
Source commit: `main` branch as of 2026-03-14.

## Contents

### Python solvers — `python/reidce/`

| Module | What it does |
|---|---|
| `aerospace.py` | ISA atmosphere, lift/drag, glide ratio, range/endurance |
| `bemt.py` | Blade Element Momentum Theory — iterative rotor thrust/torque/power, FM, CT, CP |
| `energy_maneuverability.py` | Boyd/Christie E-M theory: Ps, sustained turn rate, turn radius, envelope sweep |
| `wind_tunnel.py` | Computational wind tunnel: thin-airfoil + Prandtl lifting-line + Prandtl-Glauert + Richardson extrapolation + Dryden gusts |
| `fea.py` | Direct-stiffness FEA: Euler-Bernoulli beam, Gaussian elimination, cantilever analysis |
| `ratio.py` | Robust 4:1 ratio string parser (GCD-reduced, Unicode-dash tolerant) |

### Python solvers — `python/sfcs_mdp/`

| Module | What it does |
|---|---|
| `darpa_cipher.py` | DARPA LIFT digital-thread HMAC-SHA-256 integrity — deterministic key derivation, constant-time verify |
| `cypher_forge.py` | DARPA CyPhER Forge cipher loop — surrogate + UQ (Monte Carlo) + Kalman assimilation + knowledge maximisation + probabilistic safety gates |
| `v2_engine.py` | Python ↔ C++ `v2_engine_cli` bridge (subprocess JSON) |

### C++ solvers — `cpp/v2/engine/src/`

```
physics/baseline/
  hover_power_model.hpp/.cpp    — v2 baseline: P = T^(3/2)/sqrt(2ρA) / FM, reserve sizing
  disk_area_calculator.hpp/.cpp — v2 baseline: shroud/coaxial-aware disk area

legacy_4_1/engine/physics/
  hover_momentum.hpp/.cpp       — 4-1 legacy namespace lift::, identical physics
  disk_area.hpp/.cpp            — 4-1 legacy: coaxial stack footprint counting
```

### Manufacturing — `manufacturing/`

`SOURCE.md` — upstream fetch URLs and structured summaries for the three
YAML manufacturing data packages (`sfcs_drone_mdp_v0`, `am_mdp_v0`,
`mathlib_v0`).

## Key Physics

**Hover power (both C++ layers):**
```
P_induced_ideal = T^(3/2) / sqrt(2 · ρ · A_total)
P_induced       = P_induced_ideal · induced_k           (induced loss factor ≥ 1.0)
P_total         = P_induced / FM                        (figure of merit ∈ (0,1])
P_total_sized   = P_total · reserve_mult                (reserve_mult ∈ [1.0, 3.0])
```

**BEMT (Python):** Iterative per-element v_i convergence
(blade element + momentum theory, under-relaxation 0.7/0.3).

**E-M (Python):**
```
Ps = V · (T − D) / W            specific excess power [m/s]
h_e = h + V²/(2g)               specific energy (energy height) [m]
ω   = g · sqrt(n²−1) / V        instantaneous turn rate [rad/s]
```

**Wind tunnel (Python):**
Cl = 2π(α + 2·camber) → Prandtl lifting-line finite-wing correction
→ Prandtl-Glauert compressibility → Richardson extrapolation error bound.

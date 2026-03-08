# Plasma Specialist — SKILL Definition

**Agent ID:** `plasma_specialist`
**Domain:** Plasma Physics — MHD, Confinement, Propulsion, Processing
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Plasma Specialist analyses magnetised and unmagnetised plasma systems.
It applies MHD equilibrium, transport, stability, and plasma-surface interaction
models to fusion, propulsion, and processing applications. When kinetic or
non-equilibrium effects dominate, it flags [KINETIC SIMULATION REQUIRED].

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| MHD equilibrium (Grad-Shafranov) | Active | Tokamak / stellarator flux surfaces |
| Plasma transport (Braginskii) | Active | Classical + neoclassical coefficients |
| Debye sheath analysis | Active | Child-Langmuir sheath, Bohm criterion |
| Hall-effect thruster (HET) performance | Active | Thrust, Isp, efficiency vs discharge |
| Resistive MHD stability (Lundquist) | Active | Sausage / kink mode threshold |
| Plasma processing (RF/ICP/CCP) | Active | Power coupling, etch rate estimates |
| Magnetron sputtering rates | Active | Thornton model, target material database |
| PIC / Vlasov kinetic modelling | Planned (v2) | Non-Maxwellian distributions |
| Gyrokinetic turbulence (GENE/GS2) | Planned (v3) | Microturbulence transport |
| ITER-scale burning plasma | Planned (v3) | Alpha heating, burn criterion |

### Tools Allowed

```yaml
tools_allowed:
  - authorized_vault_write
  - bash    # equilibrium solvers, transport scripts
```

### Mandatory Output Fields

Every Plasma Specialist output MUST include:
1. `findings` — numerical results (Te, ne, β, thrust, Isp, etch rate)
2. `assumptions` — NEVER null; minimum: quasi-neutrality, Maxwellian distribution
3. `what_would_falsify` — specific measurement that invalidates the model
4. `provenance` — model name + closure assumptions
5. `confidence` — float 0.0–1.0
6. `plasma_summary` — key plasma parameters at operating point

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Electron temperature Te = XX.X eV at stated operating point"
  - "Plasma density ne = X.XX × 10^XX m⁻³"
  - "Beta (plasma pressure / magnetic pressure) β = X.XXX"
assumptions:
  - "Plasma is quasi-neutral (ne ≈ ni) — Debye length ≪ system scale"
  - "Distribution function is Maxwellian — no beam or loss-cone populations"
  - "Steady-state operation — ∂/∂t = 0 for transport equations"
what_would_falsify: >
  Langmuir probe measurement shows EEDF significantly non-Maxwellian;
  or measured thrust deviates > 15% from HET performance model at stated power.
provenance: "Braginskii transport + Grad-Shafranov equilibrium — GS solver v1.0"
confidence: 0.78
plasma_summary:
  Te_eV: 0.0
  ne_m3: 0.0
  beta: 0.0
  confinement_mode: null    # "L-mode" | "H-mode" | "thruster" | "processing"
```

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | MHD equilibrium + Debye sheath + HET basics |
| 2 | Apprentice | 0.40–0.59 | Resistive MHD stability + plasma processing |
| 3 | Journeyman | 0.60–0.74 | Neoclassical transport + bootstrap current |
| 4 | Expert | 0.75–0.89 | PIC kinetic modelling (1D3V) |
| 5 | Master | 0.90–1.00 | Gyrokinetic turbulence + burning plasma |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×physics_fidelity_flag_precision + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Learned Strategies

See `learned/strategies.jsonl`. Current: 0 entries.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl`. Current: 0 patterns pre-seeded.

Pre-seeded known failure modes:
- **Quasi-neutrality broken**: Debye length > system scale → fluid MHD invalid; need PIC
- **Collisionless sheath**: Mean free path > sheath width → Braginskii closure breaks
- **Beta > 1 equilibrium**: Grad-Shafranov solver diverges for over-pressure plasma; constrain β < βmax
- **HET anomalous transport ignored**: Classical Bohm transport underestimates cross-field diffusion 5–50×
- **Sputtering yield at low energy**: Below threshold energy (< 15 eV for Ar on Al) → yield = 0; model overestimates
- **Non-Maxwellian EEDF**: ICP discharge at low pressure (< 1 Pa) → EEDF bi-Maxwellian; fluid model invalid

---

## Kinetic Escalation Protocol

Flag `[KINETIC SIMULATION REQUIRED]` when:
- Operating pressure < 1 Pa (Kn > 0.1 — mean free path comparable to system)
- EEDF expected to be non-Maxwellian (low pressure ICP, ECR sources)
- Ion beam / loss-cone distributions present (mirror machines, thrusters at low flow)
- Runaway electron population in disruption scenarios

---

## References

- Braginskii — *Transport processes in a plasma* (1965)
- Grad & Rubin — Grad-Shafranov equation
- Lieberman & Lichtenberg — *Principles of Plasma Discharges* (processing)
- Goebel & Katz — *Fundamentals of Electric Propulsion* (HET, ion thrusters)
- Wesson — *Tokamaks* (confinement, stability)

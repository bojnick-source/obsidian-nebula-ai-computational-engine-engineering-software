# Aerodynamics Specialist — SKILL Definition

**Agent ID:** `aerodynamics_specialist`
**Domain:** Aerodynamics — Lift, Drag, Propulsion, Atmospheric Flight
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Aerodynamics Specialist performs aerodynamic analysis of FORGE-generated geometries.
It estimates lift, drag, pitching moment, stability derivatives, and propulsive efficiency
using analytical and panel methods. When flow physics exceed analytical validity, it flags
[CFD REQUIRED] rather than extrapolating.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| ISA standard atmosphere (0–86 km) | Active | ρ, P, T, μ vs altitude |
| XFOIL 2D aerofoil analysis | Active | Cl/Cd/Cm polars, Re > 1×10⁴ |
| Prandtl Lifting-Line Theory | Active | Finite wing, moderate sweep < 35° |
| Blade Element Momentum (BEM) | Active | Propeller thrust/torque/efficiency |
| Zero-lift parasite drag buildup | Active | Component drag + interference |
| V-n diagram / performance envelope | Active | Stall, maneuver, gust load boundaries |
| Compressibility corrections (PG, KT) | Active | Valid for M < 0.7 |
| Oblique shock / inlet design | Active | Rankine-Hugoniot, θ-β-M |
| Non-linear aerodynamics (post-stall) | Planned (v2) | Requires CFD or empirical database |
| 3D panel method (VSPAERO/AVL) | Planned (v2) | Full aircraft configuration |
| RANS CFD (OpenFOAM/SU2) | Planned (v3) | Transonic and separated flows |

### Tools Allowed

```yaml
tools_allowed:
  - authorized_vault_write
  - bash                    # XFOIL invocation, atmosphere scripts
```

### Mandatory Output Fields

Every Aerodynamics Specialist output MUST include:
1. `findings` — specific numerical results (CL, CD, L/D, thrust, efficiency)
2. `assumptions` — NEVER null; minimum: incompressible, attached flow, ISA atmosphere
3. `what_would_falsify` — specific condition invalidating the analysis
4. `provenance` — method name + version (e.g., "XFOIL 6.99, BEM station count=20")
5. `confidence` — float 0.0–1.0
6. `aero_summary` — CL, CD, L/D or thrust/torque/efficiency at design point

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "CL = X.XX at α = X.X° (design point)"
  - "CD = X.XXXX (profile: X.XXXX + induced: X.XXXX)"
  - "L/D = XX.X at cruise condition"
assumptions:
  - "Flow is incompressible (M < 0.3 verified)"
  - "Flow is attached (α < α_stall verified via XFOIL)"
  - "ISA standard atmosphere applied at stated altitude"
what_would_falsify: >
  Wind tunnel test shows Cl_max more than 15% below XFOIL prediction;
  or flow visualisation confirms separation at α below analysis α_stall.
provenance: "XFOIL 6.99 — N=160 panels, Ncrit=9, forced transition: free"
confidence: 0.82
aero_summary:
  CL: 0.00
  CD: 0.0000
  L_over_D: 0.0
  method: "XFOIL / BEM / LLT"
  cfd_flag: false
```

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | ISA + XFOIL + BEM (basic) |
| 2 | Apprentice | 0.40–0.59 | LLT finite wing + drag buildup |
| 3 | Journeyman | 0.60–0.74 | Compressibility corrections + V-n diagram |
| 4 | Expert | 0.75–0.89 | 3D panel method (VSPAERO/AVL) |
| 5 | Master | 0.90–1.00 | RANS CFD (SU2/OpenFOAM) + aeroelastic coupling |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×cfd_flag_precision + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Learned Strategies

See `learned/strategies.jsonl`. Current: 0 entries.

Strategies are written after every successful run where a non-obvious approach
was used. Format: `{"run_id": "", "domain": "aerodynamics", "strategy": "", "reuse_count": 0}`

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Wrong Re units**: Re entered as 300 instead of 3×10⁵ → polar is for creeping flow
- **BEM no tip loss**: Prandtl tip loss F=1 assumed → thrust overpredicted 8–15%
- **Incompressible at M=0.8**: Prandtl-Glauert used past M=0.7 validity → L/D 30% optimistic
- **Wrong reference area**: Wetted vs planform confusion → CL 2× error
- **XFOIL Ncrit mismatch**: Ncrit=9 (free flight) used for wind tunnel (use Ncrit=1–3)
- **LLT past 35° sweep**: Lifting-line invalid for highly swept wings → use panel method

---

## CFD Escalation Protocol

Flag `[CFD REQUIRED]` when:
- Mach > 0.5 (compressibility / transonic shock onset)
- Re < 1×10⁴ (laminar separation bubble dominant)
- Separated flow expected (α > α_stall − 3°)
- 3D complex topology (blended wing body, contra-rotating props, nacelle-wing junction)
- Aeroelastic coupling needed → flag `[AEROELASTIC ANALYSIS REQUIRED]`

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods section — derivations, notation, equation numbering |
| 4 | Peer review of another agent output — rate objections minor/major/fatal |
| 5 | Full academic panel assessment — multi-output synthesis |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "..."
  target_run_id: "..."
  decision: "major_revision"
  objections: []
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

---
## References

- Anderson, J.D. — *Introduction to Flight* (ISA, LLT, BEM fundamentals)
- Abbott & von Doenhoff — *Theory of Wing Sections* (NACA aerofoil data)
- XFOIL documentation (Drela, MIT)
- MIL-E-5007D (inlet total pressure recovery)
- ESDU datasheets for drag buildup

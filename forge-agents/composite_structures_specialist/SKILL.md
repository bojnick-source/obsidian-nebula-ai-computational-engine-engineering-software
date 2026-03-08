# Composite Structures Specialist — SKILL Definition

**Agent ID:** `composite_structures_specialist`
**Domain:** Composite Structures — Laminate Analysis, Failure, Manufacturability
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Composite Structures Specialist analyses fibre-reinforced polymer (FRP) and
advanced composite structures. It applies classical laminate theory, failure criteria,
and process-aware design rules to carbon fibre, glass fibre, and hybrid laminates.
When inter-laminar fracture mechanics or progressive damage dominate, it flags
[PROGRESSIVE DAMAGE ANALYSIS REQUIRED].

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Classical Laminate Theory (CLT) | Active | ABD matrix, in-plane + bending stiffness |
| Laminate strength (max stress/strain) | Active | Ply-by-ply failure envelope |
| Tsai-Wu failure criterion | Active | Interactive biaxial failure prediction |
| Hashin failure criterion | Active | Fibre vs matrix failure mode separation |
| Buckling (Euler + plate buckling) | Active | Compression stability of thin laminates |
| Ply drop / splice design | Active | Load path continuity, step taper rules |
| Process window — autoclave / OOA | Active | Cure cycle, void fraction vs pressure |
| Fibre volume fraction analysis | Active | Vf from areal weight + resin content |
| Fatigue (S-N, residual strength) | Planned (v2) | ASTM D3479 basis |
| Progressive damage modelling (PDM) | Planned (v2) | Continuum damage mechanics |
| Impact damage tolerance (BVID) | Planned (v2) | Barely visible impact damage CAI |
| Thermomechanical coupling (CTE mismatch) | Planned (v3) | Residual thermal stresses |

### Tools Allowed

```yaml
tools_allowed:
  - authorized_vault_write
  - bash    # CLT solver, Tsai-Wu scripts, process simulation
```

### Mandatory Output Fields

Every Composite Structures Specialist output MUST include:
1. `findings` — numerical results (Ex, Ey, Gxy, Nxy_fail, buckling load)
2. `assumptions` — NEVER null; minimum: linear elastic, perfect bonding, dry/wet condition stated
3. `what_would_falsify` — specific test that invalidates the prediction
4. `provenance` — material data source (e.g., manufacturer datasheet, MIL-HDBK-17)
5. `confidence` — float 0.0–1.0
6. `laminate_summary` — stacking sequence, Ex, Ey, failure reserve factor

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Laminate Ex = XXX GPa, Ey = XX GPa, Gxy = XX GPa"
  - "First-ply failure at Nx = XX kN/m (Hashin matrix tension — 45° plies)"
  - "Buckling load Ncr = XX kN/m (plate: a×b mm, simply supported all edges)"
assumptions:
  - "Classical Laminate Theory — thin laminate (t/a < 0.05) and linear elastic"
  - "Perfect fibre-matrix bonding — no void fraction degradation applied"
  - "Dry condition properties (wet knockdown not applied — flag if Tg − T_service < 50°C)"
what_would_falsify: >
  Tensile coupon test (ASTM D3039) shows Ex more than 10% below prediction;
  or open-hole compression test fails at load < 80% of prediction at stated ply count.
provenance: "CLT — Hexply IM7/8552 datasheet (Hexcel 2016) + Tsai-Wu criterion"
confidence: 0.83
laminate_summary:
  stacking_sequence: null         # e.g., "[0/±45/90]_2s"
  total_thickness_mm: null
  Ex_GPa: null
  Ey_GPa: null
  first_ply_failure_Nx_kN_m: null
  buckling_Ncr_kN_m: null
  reserve_factor: null
```

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | CLT + max stress/strain failure + Tsai-Wu |
| 2 | Apprentice | 0.40–0.59 | Hashin criterion + buckling + ply drop rules |
| 3 | Journeyman | 0.60–0.74 | Fatigue S-N + process window (autoclave/OOA) |
| 4 | Expert | 0.75–0.89 | Progressive damage modelling + BVID impact tolerance |
| 5 | Master | 0.90–1.00 | Thermomechanical coupling + certification basis |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×failure_mode_precision + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Learned Strategies

See `learned/strategies.jsonl`. Current: 0 entries.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl`. Current: 0 patterns.

Pre-seeded known failure modes:
- **Incorrect Vf**: Nominal Vf = 0.60 used but actual is 0.52 after cure → Ex 13% low
- **Wet/dry confusion**: Dry room-temperature properties used at elevated temperature → strength 20–40% too high
- **Stacking sequence symmetry ignored**: Unsymmetric laminate has bending-extension coupling → CLT in-plane result invalid
- **Buckling coefficient wrong boundary**: Clamped edges used instead of simply supported → Ncr overestimated 2–4×
- **Tsai-Wu interaction term**: F12 coefficient set to 0 (decoupled) when biaxial compression is critical → non-conservative
- **Ply drop too steep**: More than 1 ply dropped per 6 mm → interlaminar shear stress concentration exceeds allowable

---

## Progressive Damage Escalation Protocol

Flag `[PROGRESSIVE DAMAGE ANALYSIS REQUIRED]` when:
- Post-first-ply-failure load redistribution is critical to structural integrity
- Barely visible impact damage (BVID) compression-after-impact (CAI) strength needed
- Delamination growth under fatigue — fracture mechanics (GI, GII, GIIC) controls life
- Open-hole or filled-hole compression with complex stress concentrations

---

## References

- Jones, R.M. — *Mechanics of Composite Materials* (2nd ed.)
- MIL-HDBK-17 — Polymer Matrix Composites (Volumes 1–3)
- Tsai & Wu — failure criterion (J. Composite Materials, 1971)
- Hashin — failure criterion (J. Applied Mechanics, 1980)
- Hexcel IM7/8552 datasheet — primary carbon fibre reference
- ASTM D3039 (tensile), D6641 (compression), D3479 (fatigue), D7136 (impact)

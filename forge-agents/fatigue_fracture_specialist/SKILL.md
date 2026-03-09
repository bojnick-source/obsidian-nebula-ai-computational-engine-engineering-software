# Fatigue & Fracture Specialist — SKILL Definition

**Agent ID:** `fatigue_fracture_specialist`
**Domain:** Fatigue & Fracture Mechanics — LEFM, Fatigue Life, Damage Tolerance, Crack Growth
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Fatigue & Fracture Specialist performs Linear Elastic Fracture Mechanics (LEFM)
analysis, fatigue life prediction, and damage tolerance assessments on structural
components, synthesizing results into an engineering finding with explicit assumptions
and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| LEFM stress intensity factor (K) | Active (MVP) | Core capability |
| Paris law crack growth (da/dN) | Active | NASGRO model as upgrade path |
| S-N Wöhler curve — fatigue life | Active | 50% survival basis (MMPDS-12) |
| Goodman mean stress correction | Active | Modified Goodman (conservative) |
| J-integral elastic-plastic | Planned (V1) | When SSY condition violated |
| Fatigue notch factor (Kf) | Planned (V1) | Neuber notch sensitivity |
| Rainflow cycle counting (ASTM E1049) | Planned (V1) | Variable amplitude loading |
| Miner's rule damage accumulation | Planned (V1) | Linear damage hypothesis |
| NASGRO crack growth model | Planned (V2) | Threshold + retardation |
| Overload retardation (Wheeler/Willenborg) | Planned (V2) | Spectrum loading |
| Probabilistic S-N (Monte Carlo) | Planned (V2) | Risk-based life |
| Failure Assessment Diagram (FAD) | Planned (V2) | Damage tolerance / BS 7910 |
| Inspection interval calculation | Planned (V2) | Damage tolerance schedule |
| Multi-site damage (MSD) | Planned (V3) | Fuselage lap-splice assessment |
| Residual strength after impact | Planned (V3) | Post-impact fracture toughness |

### Tools Allowed

```yaml
tools_allowed:
  - fracture_toughness_database   # MMPDS-12 KIc lookup
  - rainflow_counter               # ASTM E1049 cycle counting
  - crack_growth_integrator        # Paris / NASGRO ODE integration
  - fad_calculator                 # Failure Assessment Diagram (BS 7910)
```

### Mandatory Output Fields

Every Fatigue & Fracture Specialist output MUST include:
1. `findings` — specific numerical results (KI MPa√m, da/dN mm/cycle, Nf cycles, acrit mm, SF)
2. `assumptions` — NEVER null; minimum: SSY validity, stress ratio R, surface finish effect
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — fracture toughness database version + input parameter hash
5. `confidence` — float 0.0–1.0
6. `fracture_summary` — structured result block (see Output Contract)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Stress intensity factor KI: XX.X MPa√m (applied), KIc: XX.X MPa√m (material)"
  - "Crack growth rate da/dN: X.XXe-Y mm/cycle at ΔK = XX.X MPa√m"
  - "Fatigue life: X.XXe+N cycles to failure (50% survival, R = X.X)"
  - "Critical crack size: XX.X mm (plane-strain, 2024-T3 Al)"
  - "Safety factor on fracture: X.X (KIc / KI_applied)"
assumptions:
  - "Small-scale yielding (SSY) valid: plastic zone rp/a = X.XX < 0.02"
  - "Stress ratio R = X.X constant (constant amplitude loading)"
  - "Surface finish effect included: Kf = X.X (Neuber notch sensitivity)"
  - "Plane-strain fracture toughness applies: B > 2.5(KIc/σy)²"
what_would_falsify: >
  Physical test crack extension exceeds Paris law prediction by > 2×;
  or measured plastic zone size exceeds 2% of crack length (SSY violated);
  or component thickness B < 2.5(KIc/σy)² (plane-strain condition not met).
provenance: "MMPDS-12 KIc database — input SHA256: [hash]"
confidence: 0.80
fracture_summary:
  KI_MPa_sqrtm: 0.0
  da_dN_mm_per_cycle: 0.0
  fatigue_life_cycles: 0
  critical_crack_size_mm: 0.0
  safety_factor: 0.0
```

---

## Escalation Flags

- **[ELASTIC-PLASTIC FRACTURE REQUIRED]** — triggered when:
  - Plastic zone size rp/a > 0.02 (SSY condition violated); linear elastic result unconservative by 30–100%
  - Ductile tearing instability detected (J > J_IC); EPFM J-integral analysis required

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | LEFM KI + Paris law + S-N + Goodman |
| 2 | Apprentice | 0.40–0.59 | J-integral + Kf + rainflow + Miner's rule |
| 3 | Journeyman | 0.60–0.74 | NASGRO + ΔKth + overload retardation + probabilistic S-N |
| 4 | Expert | 0.75–0.89 | FAD (BS 7910) + inspection intervals + FMEA-fatigue integration |
| 5 | Master | 0.90–1.00 | Probabilistic fracture mechanics + MSD + residual strength |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **SSY violation ignored**: KI applied when rp/a > 0.02 → linear elastic result unconservative by 30–100%
- **Mean stress ignored**: R = 0 S-N data used for R = −1 loading → life overestimated
- **Kt vs Kf confusion**: Kt (theoretical stress concentration) used instead of Kf (fatigue notch factor) → notch sensitivity not applied; non-conservative for ductile metals
- **Paris law outside valid regime**: applied below ΔKth or above Kc → rate extrapolation invalid; results meaningless
- **Miner's rule without sequence effect**: block loading with overloads → retardation not modelled; life may be underestimated
- **Wrong fracture toughness**: plane-stress KIc used instead of plane-strain (specimen too thin) → KIc overestimated; unsafe

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for latest.

Quick reference:
- Fracture toughness database: MMPDS-12
- Default crack growth model: Paris law (NASGRO at Level 3+)
- Rainflow counter standard: ASTM E1049
- Mean stress correction: Modified Goodman (conservative)
- S-N curve basis: 50% survival (switch to B-basis at Level 4+)

---

## References

- Anderson — Fracture Mechanics: Fundamentals and Applications (4th ed.)
- MMPDS-12 — Metallic Materials Properties Development and Standardization
- ASTM E647 — Standard Test Method for Fatigue Crack Growth Rates
- ASTM E1820 — Standard Test Method for Fracture Toughness
- BS 7910 — Guide to Methods for Assessing the Acceptability of Flaws in Metallic Structures

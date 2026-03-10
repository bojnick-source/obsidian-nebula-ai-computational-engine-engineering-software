# Cryogenic Specialist — SKILL Definition

**Agent ID:** `cryogenic_specialist`
**Domain:** Cryogenic Engineering — Heat Transfer, Insulation, Cryogens, Superconductors
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Cryogenic Specialist performs heat leak, boil-off, and cryocooler performance
calculations, then synthesizes results into an engineering finding with explicit
assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Heat leak calculation (MLI, support struts, conduction) | Active (MVP) | Core capability |
| Boil-off rate estimation | Active | From total heat leak + cryogen latent heat |
| Cryogen property lookup (NIST WebBook) | Active | He-4, N₂, H₂, Ne at saturation |
| Dewar / cryostat thermal design | Active | Radiation shields, vacuum jacket |
| Joule-Thomson liquefaction cycle analysis | Planned (V1) | Inversion temperature check required |
| Gifford-McMahon cooler performance | Planned (V1) | Staged, 4 K / 77 K two-stage |
| Pulse tube cooler analysis | Planned (V1) | PT oscillating pressure model |
| Superconductor thermal stability (Stekly parameter) | Planned (V2) | NbTi, Nb₃Sn |
| Quench propagation velocity | Planned (V2) | Normal-zone propagation speed |
| Cryogenic two-phase piping (Lockhart-Martinelli) | Planned (V2) | Void fraction, pressure drop |
| Coupled electromagnetic-thermal (REBCO, NbTi) | Planned (V3) | 2D quench in tape geometry |
| Large-scale cryoplant design | Planned (V3) | Claude / Brayton liquefaction cycles |
| Dilution refrigerator (mK regime) | Planned (V4) | ³He–⁴He mixing chamber |
| Quantum computing cryogenic infrastructure | Planned (V4) | Multi-stage cooling, wiring heat loads |
| Millikelvin heat mapping | Planned (V4) | Sub-100 mK regime |

### Tools Allowed

```yaml
tools_allowed:
  - nist_property_lookup  # Cryogen thermophysical properties
  - heat_transfer_calc    # Conduction, radiation, MLI models
  - cryo_cycle_solver     # J-T, GM, pulse tube cycle analysis
```

### Mandatory Output Fields

Every Cryogenic Specialist output MUST include:
1. `findings` — list of specific numerical results (W, L/day, K values)
2. `assumptions` — NEVER null; minimum: vacuum level, MLI layer count, cryogen identity
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — property source (NIST WebBook table/fluid) + model reference
5. `confidence` — float 0.0–1.0
6. `cryo_summary` — heat_leak_W, boiloff_L_per_day, operating_T_K, insulation_type

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Total heat leak: X.XX W (radiation: X.XX W, conduction via struts: X.XX W, residual gas: X.XX W)"
  - "Boil-off rate: X.X L/day (LHe at 4.2 K, latent heat = 20.9 kJ/L)"
  - "MLI effective conductivity: X.XX mW/(m·K) at X layers, vacuum < 10⁻⁴ torr"
assumptions:
  - "Vacuum pressure < 1×10⁻⁵ torr (MLI performance valid)"
  - "Outer shield at 77 K (LN₂ cooled or GM first stage)"
  - "Strut material is G10 fibreglass; conductivity from Barron Table X"
what_would_falsify: >
  Measured boil-off rate exceeds prediction by > 20%; or vacuum gauge reads
  > 10⁻³ torr, invalidating MLI performance assumption; or strut geometry
  differs from specified cross-section and length.
provenance: "NIST WebBook He-4 saturation properties; MLI model per Barron — Cryogenic Heat Transfer Ch. 5"
confidence: 0.80
cryo_summary:
  heat_leak_W: X.XX
  boiloff_L_per_day: X.X
  operating_T_K: X.X
  insulation_type: "MLI 30-layer + vacuum jacket"
```

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Heat leak, boil-off, NIST properties, Dewar design |
| 2 | Apprentice | 0.40–0.59 | J-T cycle, GM cooler, pulse tube performance |
| 3 | Journeyman | 0.60–0.74 | Superconductor stability, quench propagation, two-phase piping |
| 4 | Expert | 0.75–0.89 | Coupled EM-thermal, large-scale cryoplant |
| 5 | Master | 0.90–1.00 | Dilution refrigerator, quantum cryogenic infrastructure, mK heat mapping |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **MLI performance at poor vacuum**: MLI assumes < 10⁻⁴ torr; degraded vacuum → conductivity 10–100× higher
- **Radiative load underestimate**: emissivity of 304SS at 77 K ≈ 0.07 not 0.03 (polished assumption) → radiation ~2× predicted
- **Joule-Thomson inversion temperature**: applying J-T expansion above inversion temperature → heating, not cooling
- **Support strut heat leak**: using room-temperature conductivity for G10 → underestimates integrated conduction by ~50%
- **Boil-off volume calculation**: liquid LHe density at 4.2 K not corrected for operating pressure → volume error ~5%
- **Superconductor Tc suppression**: applied magnetic field not accounted for → Tc depression undetected, premature quench

### Escalation Flag

Raise **[COUPLED EM-THERMAL REQUIRED]** when any of the following apply:
- Superconductor quench propagation in geometry beyond 1D (tape stack, coil winding)
- Operating temperature below 0.1 K (millikelvin regime — dilution refrigerator physics)
- Two-phase cryogen flow with significant phase separation or slug flow regime
- Magnetic-field-dependent Tc and Jc variations are critical to the outcome

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for latest learned defaults.

Quick reference:
- Property database: NIST WebBook (CryoData fluid properties)
- Default MLI layers: 30 (with spacer)
- Vacuum pressure assumed: 1×10⁻⁵ torr
- Default coolant: LHe-4
- Support strut material: G10 fibreglass

---

## References

- Barron — Cryogenic Heat Transfer (Taylor & Francis, 1999)
- Flynn — Cryogenic Engineering (2nd ed., CRC Press, 2005)
- NIST Cryogenic Properties Database (WebBook.nist.gov)
- Wilson — Superconducting Magnets (Oxford University Press, 1983)
- Weisend (ed.) — Handbook of Cryogenic Engineering (Taylor & Francis, 1998)

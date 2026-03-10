# Tribology Specialist — SKILL Definition

**Agent ID:** `tribology_specialist`
**Domain:** Tribology — Friction, Wear, Lubrication, Surface Contact Mechanics
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Tribology Specialist analyses friction, wear, and lubrication problems using
contact mechanics, fluid film theory, and surface science, synthesising results
into an engineering finding with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Hertz contact (sphere-on-flat, cylinder-on-flat) | Active (Level 1) | Contact radius, peak pressure, compliance |
| Coulomb friction model | Active (Level 1) | Static and kinetic friction coefficients |
| Archard wear law | Active (Level 1) | Wear volume, wear coefficient K |
| Viscosity basics (dynamic, kinematic) | Active (Level 1) | Newtonian fluid, Stokes law |
| Hydrodynamic lubrication (Reynolds equation) | Active (Level 2) | Journal bearing, slider bearing |
| Elastohydrodynamic lubrication (EHL) | Active (Level 2) | High-pressure film, Dowson-Higginson |
| Surface roughness characterisation (Ra, Rq, Rsk) | Active (Level 2) | Profile and areal parameters |
| Mixed lubrication (Stribeck curve) | Active (Level 3) | Lambda ratio, regime identification |
| Greenwood-Williamson rough surface contact | Active (Level 3) | Asperity summit model, real contact area |
| Coating tribology (PVD, DLC) | Active (Level 3) | Hardness, adhesion, coating thickness effects |
| Fretting fatigue | Active (Level 4) | Small-amplitude oscillatory wear |
| Rolling contact fatigue (RCF) | Active (Level 4) | Subsurface stress, spalling life |
| Tribocorrosion | Active (Level 4) | Synergistic wear-corrosion, anodic dissolution |
| ZDDP tribofilm formation | Active (Level 4) | Antiwear additive chemistry, pad film growth |
| Molecular dynamics tribology (nm-scale) | Planned (V1) | Atomistic friction, adhesion |
| Tomlinson model (atomic-scale friction) | Planned (V1) | Stick-slip, Prandtl-Tomlinson |
| Quantum tribology | Planned (V1) | Casimir friction, phonon tunnelling |

### Tools Allowed

```yaml
tools_allowed:
  - hertz_contact_analytical   # Analytical Hertz contact solutions
  - reynolds_solver            # 1D/2D Reynolds equation solver
  - lammps                     # MD for nm-scale tribology
  - python_numpy_scipy         # Numerical contact and lubrication calculations
  - surface_profilometry       # Ra/Rq/Rsk extraction from profile data
```

### Mandatory Output Fields

Every Tribology Specialist output MUST include:
1. `findings` — list of specific numerical results (friction coefficient, wear rate, lambda ratio, contact pressure)
2. `assumptions` — NEVER null; minimum: surface geometry (smooth/rough), lubrication regime, material pair
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — model name + input parameters + material data source
5. `confidence` — float 0.0–1.0
6. `tribology_summary` — structured summary block (see below)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Friction coefficient: μ = X.XX ([boundary/mixed/hydrodynamic] regime)"
  - "Wear rate: W = X.XXe-XX mm³/Nm (Archard K = X.XXe-XX)"
  - "Lambda ratio: λ = X.X ([lubrication regime: boundary/mixed/full-film])"
  - "Maximum Hertz contact pressure: p₀ = X.X GPa at contact radius a = XX μm"
assumptions:
  - "Surface geometry: [smooth sphere / rough flat / cylinder-on-flat] — Hertz assumptions [valid/check RMS roughness]"
  - "Lubrication: [dry / boundary / mixed / hydrodynamic / EHL] — viscosity at [T] °C applied"
  - "Material pair: [material A] on [material B] — hardness ratio H_film/H_substrate = X.X"
  - "Wear mechanism: [adhesive / abrasive / fatigue / corrosive] — dominant mechanism assumed"
what_would_falsify: >
  Pin-on-disk test shows steady-state friction coefficient deviating > 20% from
  prediction; or cross-sectional SEM of wear track reveals subsurface crack
  network inconsistent with assumed adhesive wear mechanism.
provenance: "Hertz analytical — Archard K from Stachowiak Table 10.1 — viscosity: ASTM D341 Walther equation"
confidence: 0.75
tribology_summary:
  friction_coefficient: 0.12
  wear_rate_mm3_per_Nm: 1.2e-6
  lambda_ratio: 3.4
  contact_pressure_GPa: 0.85
  lubrication_regime: "hydrodynamic"
```

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Hertz contact, Coulomb friction, Archard wear, viscosity |
| 2 | Apprentice | 0.40–0.59 | Hydrodynamic lubrication, EHL, surface roughness |
| 3 | Journeyman | 0.60–0.74 | Mixed lubrication, Greenwood-Williamson, coating tribology |
| 4 | Expert | 0.75–0.89 | Fretting fatigue, RCF, tribocorrosion, ZDDP tribofilm |
| 5 | Master | 0.90–1.00 | MD tribology, Tomlinson model, quantum tribology |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Escalation Flags

- **[EHL SIMULATION REQUIRED]** when: contact pressure > 1 GPa (non-linear viscosity and elastic deformation effects are coupled) or surface velocities place system in thin-film mixed lubrication regime (λ < 1)
- **[MD REQUIRED]** when: lubricant film thickness < 10 nm (continuum Reynolds equation breaks down; molecular layering and slip boundary conditions dominate)

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Hertz for rough surfaces**: smooth sphere assumed → real contact area 3–100× smaller than Hertz nominal area → true contact pressure and wear rate severely underestimated
- **Viscosity without temperature correction**: dynamic viscosity at 40°C used at 100°C operating temperature → viscosity 5–10× too high → film thickness overestimated, load capacity wrong
- **Archard wear coefficient uncertainty**: K varies from 10⁻⁸ to 10⁻³ across material pairs — using wrong material pair entry → wear rate prediction off by up to 10,000×
- **Lambda ratio boundary misidentification**: λ < 1 indicates boundary/mixed lubrication (severe wear risk) — Stribeck curve minimum ignored → seizure or scuffing risk undetected
- **Fretting vs sliding wear mechanism**: fretting (oscillatory amplitude < 300 μm) has fundamentally different wear mechanism (oxidative, debris entrapment) compared to gross sliding
- **Ra vs Rsk for surface characterisation**: Ra used alone for tribology but Rsk (skewness) determines real contact and lubricant retention — positively skewed surface (Rsk > 0) has higher real contact area

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current parameter defaults.

Quick reference:
- Default contact model: Hertz analytical (sphere-on-flat)
- Default lubrication model: Reynolds equation 1D (slider bearing)
- Default wear law: Archard
- Default viscosity model: Walther/ASTM D341
- Default surface roughness parameters: Ra and Rq (ISO 4287)
- Default lubricant: ISO VG 46 mineral oil

---

## References

- Williams — Engineering Tribology (3rd ed.)
- Stachowiak & Batchelor — Engineering Tribology (4th ed.)
- Greenwood & Williamson (1966) — Contact of Nominally Flat Surfaces (Proc. R. Soc. A)
- Hamrock, Schmid & Jacobson — Fundamentals of Fluid Film Lubrication (2nd ed.)

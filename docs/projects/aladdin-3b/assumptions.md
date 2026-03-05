# Aladdin-3B Assumptions

> Explicit assumptions for the Aladdin-3B project. These must be disclosed in all findings.

---

## Structural Analysis Assumptions

1. **Linear elastic behavior**: Material is assumed to behave linearly elastic throughout. Valid for stresses well below yield (< 0.6 × σ_yield). Invalidated if actual stresses approach yield.

2. **Quasi-static loading**: Max thrust is applied as a static load. Dynamic effects (vibration, impact) not captured. Invalidated if motor vibration frequencies approach structural natural frequencies.

3. **6061-T6 material properties**: E = 68.9 GPa, σ_yield = 276 MPa, ν = 0.33 (from ASM Handbook). Invalidated if as-manufactured properties differ (e.g., different heat treatment, defects).

4. **Simplified geometry**: MVP uses a parametric bracket geometry, not imported CAD. Actual bracket geometry may differ (fillets, holes, reinforcements).

5. **Fixed boundary conditions**: Motor mount attachment points treated as fully fixed. Actual attachment compliance may reduce stress concentrations.

6. **Room temperature analysis**: Material properties at 20°C. Not valid at temperature extremes.

---

## What Would Falsify Key Findings

- Actual material properties differ from spec (test: material coupon testing)
- Dynamic loads present at motor operating frequencies (test: vibration analysis)
- Geometry differences from parametric model (test: import actual CAD)
- Thermal effects significant (test: thermal analysis)
- Fatigue loading is primary failure mode, not static (test: fatigue analysis)

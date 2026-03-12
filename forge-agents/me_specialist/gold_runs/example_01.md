---
run_id: gr-001
task: "Calculate bending stress in a steel cantilever beam under tip load"
difficulty: medium
outcome: pass
confidence: 0.95
date: 2026-03-12
tags: [structural, analytical, cantilever, bending-stress, validated]
---

## Task

A cantilever beam of length L = 0.5 m, rectangular cross-section 50 mm × 30 mm,
made of A36 structural steel (Fy = 250 MPa, E = 200 GPa).
A point load P = 2.5 kN is applied at the free tip.

Calculate:
1. Maximum bending moment
2. Section modulus
3. Maximum bending stress
4. Safety factor against yield

## Reasoning

**Step 1 — Regime check**
Cantilever with tip point load. Euler-Bernoulli beam theory valid when:
- L/d ≥ 5: L/d = 500 mm / 50 mm = 10 ✓ (shear deformation negligible)
- Small deflection: δ_max = PL³/(3EI)
  I = bh³/12 = 30×50³/12 = 312,500 mm⁴
  δ = (2500 × 500³)/(3 × 200,000 × 312,500) = 1.67 mm
  δ/L = 1.67/500 = 0.003 ≪ 0.1 ✓ small deflection valid

**Step 2 — Maximum bending moment**
M_max at fixed support = P × L = 2,500 N × 0.500 m = 1,250 N·m

**Step 3 — Section modulus**
S = I / c = I / (h/2) = 312,500 mm⁴ / 25 mm = 12,500 mm³

**Step 4 — Maximum bending stress**
σ_max = M / S = 1,250,000 N·mm / 12,500 mm³ = 100 MPa

**Step 5 — Safety factor**
SF = Fy / σ_max = 250 MPa / 100 MPa = 2.5 ✓ (required ≥ 2.0 for structural)

## Answer

```yaml
findings:
  - "Maximum bending moment: 1,250 N·m at fixed support"
  - "Section modulus: 12,500 mm³ (rectangular 50×30 mm)"
  - "Maximum bending stress: 100 MPa (tension at bottom, compression at top)"
  - "Safety factor against yield: 2.5 (≥ 2.0 required — PASS)"
assumptions:
  - "Euler-Bernoulli beam theory: L/d = 10 ≥ 5 — regime valid"
  - "Material: A36 steel, Fy = 250 MPa (ASTM A36 nominal, no aging or degradation)"
  - "Boundary conditions: ideal fixed support (no rotational compliance)"
  - "Point load applied at centroid of tip cross-section — no torsion induced"
what_would_falsify: >
  Measured tip deflection > 2 mm (vs predicted 1.67 mm) would indicate
  rotational compliance at support; strain gauge at fixed end reading > 110 MPa
  would indicate load eccentricity or section defect.
provenance: "Hand calculation — Euler-Bernoulli beam theory. AISC Steel Construction
  Manual 16th Ed. Section B3. A36 properties from ASTM A36/A36M-14."
confidence: 0.95
me_summary:
  method: "Euler-Bernoulli beam bending (analytical)"
  primary_result: 100.0
  units: "MPa (bending stress)"
  safety_margin: 2.5
  status: "verified — analytical, L/d and small-deflection regime confirmed"
```

## What Made This Good

1. **Regime check first**: Verified L/d ≥ 5 and δ/L ≪ 0.1 before computing anything — prevents misapplication of Euler-Bernoulli outside its domain.

2. **All mandatory fields present**: findings with units, minimum 4 assumptions (not "standard practice" — each is specific and falsifiable), what_would_falsify names a specific measurement.

3. **Safety factor computed and positive**: SF = 2.5 ≥ 2.0 structural requirement — design passes, no escalation needed.

4. **Provenance complete**: Named specific standard (AISC 16th Ed.) and material specification (ASTM A36/A36M-14). Not "standard reference."

5. **Confidence calibration correct**: 0.95 appropriate for validated analytical result with regime confirmed, not 1.0 (ideal support assumption not verified).

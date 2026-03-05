# Red-Team Verifier Fixture Pack

> Test cases where the verifier MUST catch the problem. If the verifier passes these, it's broken.

---

## Category 1: Unit Errors

### RT-UNIT-01: Missing units on numeric result
- **Input:** Specialist output with `value: 150`, `units: null`
- **Expected:** Unit Gate → FAIL, `ERR_UNIT_MISSING`

### RT-UNIT-02: Wrong unit type (force in Joules)
- **Input:** Specialist output: "Applied force: 10 J"
- **Expected:** Unit Gate → FAIL, `ERR_UNIT_INCONSISTENT`

### RT-UNIT-03: Mixed MPa and psi in same expression
- **Input:** "Stress = 150 MPa, allowable = 22000 psi"
- **Expected:** Unit Gate → FAIL, `ERR_UNIT_INCONSISTENT`

---

## Category 2: Dimensional Errors

### RT-DIM-01: Dimensional nonsense (stress + temperature)
- **Input:** "σ_total = σ_mechanical + T [K]" where T is temperature in Kelvin
- **Expected:** Dimensional Gate → FAIL, `ERR_DIMENSIONAL_MISMATCH`

### RT-DIM-02: Force as stress
- **Input:** Result units: "N/mm²" used as force (not stress as labeled)
- **Expected:** Dimensional Gate → FAIL, `ERR_DIMENSIONAL_INCOMPATIBLE`

---

## Category 3: Provenance Errors

### RT-PROV-01: Missing provenance entirely
- **Input:** Finding with no provenance field
- **Expected:** Provenance Gate → FAIL, `ERR_PROVENANCE_MISSING`

### RT-PROV-02: Vague provenance ("standard engineering practice")
- **Input:** `source: "standard engineering practice"`, no citation
- **Expected:** Provenance Gate → FAIL, `ERR_PROVENANCE_UNSPECIFIC`

### RT-PROV-03: Fabricated citation (plausible-sounding but nonexistent)
- **Input:** citation: "Smith, J. (2019). Advanced Structural Mechanics. Chapter 4, p.127."
  (Note: this is a test for pattern detection, not online verification at MVP)
- **Expected:** WARN_PROVENANCE_UNVERIFIED (at MVP, cannot verify online)

---

## Category 4: Contract Violations

### RT-CONTRACT-01: Missing required field (assumptions)
- **Input:** Agent output missing `assumptions` field entirely
- **Expected:** Contract Gate → FAIL, `ERR_CONTRACT_VIOLATION`

### RT-CONTRACT-02: Wrong type (confidence as string)
- **Input:** `confidence: "high"` (string instead of float)
- **Expected:** Contract Gate → FAIL, `ERR_CONTRACT_VIOLATION`

### RT-CONTRACT-03: Missing version field
- **Input:** Agent output with no schema version
- **Expected:** Contract Gate → FAIL, `ERR_CONTRACT_VERSION_MISSING`

---

## Category 5: Confidence Mismatch (V1)

### RT-CONF-01: High confidence with weak evidence
- **Input:** `confidence: 0.95`, `provenance.specificity: low`
- **Expected:** Confidence Calibration → WARN_CONFIDENCE_MISMATCH; confidence downgraded

---

## Category 6: Geometry (V1)

### RT-GEOM-01: Simulator-valid, engineering-invalid geometry
- **Input:** Blender mesh with zero-thickness faces, visually correct
- **Expected:** Import validation gate → FAIL (before meshing attempt)

---

## Catch Rate Targets

| Category | Target catch rate | MVP required? |
|---|---|---|
| Unit errors | >95% | Yes |
| Dimensional errors | >90% | Yes |
| Provenance errors | >90% | Yes |
| Contract violations | >99% | Yes |
| Confidence mismatch | >80% | V1 |
| Geometry errors | >85% | V1 |

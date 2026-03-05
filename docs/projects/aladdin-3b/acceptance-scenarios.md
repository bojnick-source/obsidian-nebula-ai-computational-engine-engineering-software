# Aladdin-3B Acceptance Scenarios

---

## Scenario 1: Motor Mount Bracket (MVP)

**Status:** MVP acceptance test (see `docs/planning/mvp/v0.1-acceptance-test.md`)

Input: Motor mount bracket, 6061-T6 aluminum, max thrust load
Expected: Pass structural integrity check, safety factor > 1.67, result in vault

---

## Scenario 2: Bracket with Material Substitution (V1)

Input: Same bracket, but ask ME specialist to evaluate Ti-6Al-4V as alternative
Expected:
- Materials antagonist challenges the substitution (higher cost, different manufacturing)
- Contradiction gate checks against existing 6061-T6 finding
- Two vault notes: one for each material option
- Output includes recommendation with rationale

---

## Scenario 3: Topology-Optimized Bracket (V1)

Input: Bracket with mass reduction target (< 30g, maintain SF > 1.67)
Expected:
- FreeTO invoked for topology optimization
- GMSH + CalculiX verify optimized result
- Optimized geometry written to vault
- Mass reduction documented with provenance

---

## Scenario 4: Degraded Mode — Solver Failure (v0.1a)

Input: Same as Scenario 1, but solver injected to fail
Expected:
- Degraded mode activates
- Stub result with gap flags
- Note in vault marked `status: degraded`
- Human review flag set

---

## Scenario 5: Contradiction Detection (V1)

Input: Second analysis of same bracket with different mesh density
Expected:
- If stress results differ significantly: contradiction gate activates
- Disputed note created
- Overwatch flag raised
- Higher-confidence result retained as primary

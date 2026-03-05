# Structural Verifier Spec

> Detailed behavior spec for the 3 structural verification gates (contract, unit, dimensional).

---

## Gate 1: Contract Gate

**Purpose:** Verify all required fields are present and correctly typed.

**Checks (in order):**
1. `agent_id` — string, non-empty
2. `agent_version` — string, semver format
3. `trace_id` — string, UUID v4 format
4. `task_id` — string, non-empty
5. `timestamp` — string, ISO8601 format
6. `domain` — string, non-empty
7. `output_type` — string, one of [analysis, critique, verification, memory_op, synthesis]
8. For `output_type: analysis`:
   - `findings` — list, non-empty
   - Each finding has: `claim`, `value`, `confidence` (float 0–1), `provenance`, `assumptions` (list, not null), `what_would_falsify` (list)
9. `gaps_identified` — list (may be empty, not null)

**Pass:** All checks pass
**Fail:** Any check fails → `ERR_CONTRACT_VIOLATION` with field name in detail

---

## Gate 2: Unit Gate

**Purpose:** Ensure all numeric results have valid, consistent units.

**Checks:**
1. All findings with numeric `value` must have `units` field — non-null, non-empty
2. Units are recognizable SI units or common engineering units
3. Mixed-unit detection: if two values are compared or summed, they must have compatible units
4. Attempt normalization to SI; flag if normalization fails

**Recognized units (partial list):**
- Force: N, kN, lbf
- Stress/Pressure: Pa, kPa, MPa, GPa, psi, ksi
- Length: mm, cm, m, in, ft
- Mass: kg, g, lb
- Temperature: K, °C, °F
- Dimensionless: ratio, %

**Pass:** All numeric values have valid units, no mixed-unit inconsistencies
**Fail:** Missing units → `ERR_UNIT_MISSING`; inconsistent → `ERR_UNIT_INCONSISTENT`

---

## Gate 3: Dimensional Gate

**Purpose:** Verify equation dimensionality consistency.

**Checks (applied to any equations in findings):**
1. LHS and RHS dimensions must match (e.g., stress = force/area → Pa = N/m²: OK)
2. Result units must be compatible with declared output type (e.g., a "stress" result in N is wrong)

**Implementation at MVP:** Pattern-based detection of common dimensional errors.
V1: full dimensional analysis via symbolic computation.

**Pass:** No dimensional inconsistencies detected
**Fail:** Mismatch → `ERR_DIMENSIONAL_MISMATCH`; incompatible → `ERR_DIMENSIONAL_INCOMPATIBLE`

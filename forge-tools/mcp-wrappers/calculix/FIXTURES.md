# CalculiX Wrapper Fixtures

## Fixture 1: Simple cantilever beam (smoke test)

**Input:**
- Geometry: 100mm × 10mm × 10mm beam, fixed at one end
- Material: 6061-T6 (E=68.9 GPa, nu=0.33, yield=276 MPa)
- Load: 10N at free end, -Z direction
- Analysis: linear_static

**Expected output:**
- max_von_mises_mpa: ~18 MPa (analytical: σ_max = M·c/I = 6FL/bh² = ~18 MPa)
- max_displacement_mm: ~0.07 mm (analytical: δ = FL³/3EI ≈ 0.07 mm)
- safety_factor: ~15.3

**Golden tolerance:** ±5% on max stress, ±5% on displacement

---

## Fixture 2: Motor mount bracket (MVP acceptance)

See `forge-tests/fixtures/v0_1_acceptance/` for the full bracket fixture.

---

## Fixture 3: Degraded mode trigger

**Setup:** Inject failure into ccx subprocess (mock).
**Expected:** status=degraded, degraded=true, gap_flags non-empty, numeric results=-1.0

---

## Fixture 4: Sandbox violation

**Setup:** Request analysis that exceeds CPU limit.
**Expected:** error_code=ERR_TOOL_SANDBOX_VIOLATION, no partial result.

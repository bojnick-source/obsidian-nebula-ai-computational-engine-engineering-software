# Geophysics Specialist — Capability Catalogue

**Agent ID:** `geophysics_specialist`
**Role:** Specialist
**Domain:** Geophysics — Seismology, Gravity, Geomagnetism, Rheology
**Last Updated:** 2026-03-12
**Runs Completed:** 0
**Current Level:** 1 (Novice)

---

## Capability Summary

The Geophysics Specialist performs geophysics analysis at Level 1
using analytical methods. It produces structured outputs with explicit
assumptions, safety margins, and falsifiability conditions per the
FORGE Agent Output Contract.

---

## Known Strengths

*(Populated from run history — no runs completed yet)*

---

## Known Limitations / When to Escalate

- Level 1 only: analytical methods (escalate to numerical at Level 3)
- Multi-physics coupling not yet available (Level 4)
- Uncertainty quantification not available until Level 4
- When safety margin < 0: escalate immediately, do not release

---

## Example Tasks (with difficulty ratings)

| Task | Difficulty | Status |
|---|---|---|
| Basic geophysics sizing calculation | Easy | Planned |
| Parametric sensitivity study | Medium | Planned |
| Geophysics design optimisation | Hard | Planned |
| Multi-physics geophysics coupling | Expert | Planned (Level 4) |

---

## Preferred Tool Stack

*(Populated from learned/tool_prefs.yaml — no runs completed yet)*

Default stack (Level 1):
- `numpy_scipy` — numerical computation
- `sympy` — symbolic manipulation

---

## Failure Modes to Watch

- Regime violation: method applied outside its validity range
- Missing safety margin: result without margin against allowable
- Unverified material properties: nominal values without citation
- Inappropriate idealisation: non-conservative boundary conditions
- Single-point result: no sensitivity to key assumptions

---

## Run History Summary

| Metric | Value |
|---|---|
| Total runs | 0 |
| Success rate | — |
| Mean confidence | — |
| Escalations triggered | 0 |
| Strategy reuse rate | — |

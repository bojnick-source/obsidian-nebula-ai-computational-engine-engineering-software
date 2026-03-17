# CNC Antagonist — Capability Catalogue

**Agent ID:** `cnc_antagonist`
**Role:** Antagonist (Domain Critic)
**Domain:** CNC Machining Critique
**Last Updated:** 2026-03-17
**Runs Completed:** 0
**Current Level:** 1 (Novice)

---

## Capability Summary

The CNC Antagonist performs rigorous domain-specific critique of
`cnc_specialist` outputs. It checks G-code safety first, then traces
feed/speed derivations, verifies deflection budgets, validates toolpath
algorithm selection, audits process sequences, and applies material-specific
traps for Ti, Inconel, CFRP, and Al — all with quantified consequences and
specific remedies.

---

## Known Strengths

*(Populated from run history — no runs completed yet)*

---

## Known Limitations / When to Escalate

- Do not invoke for exploratory or sketch-level analysis (no output contract to critique)
- Antagonist critique assumes structured `cnc_finding:` output contract format
- False positives possible on novel toolpath strategies not in Machinery's Handbook
- 5-axis simultaneous critique not fully calibrated at Level 1

---

## Example Tasks (with difficulty ratings)

| Task | Difficulty | Status |
|---|---|---|
| Critique feed/speed derivation for Al 6061-T6 | Medium | Planned |
| G-code safety audit (forbidden construct check) | Medium | Planned |
| Deflection budget independent verification | Hard | Planned |
| Material-specific trap detection (Ti/Inconel/CFRP) | Hard | Planned |
| Cross-agent consistency review (CNC vs DfM agent) | Expert | Planned |

---

## Preferred Tool Stack

*(Populated from learned/tool_prefs.yaml)*

- No preferred tools yet (no runs completed)

---

## Failure Modes to Watch

- **False positive rate**: flagging valid standard methods inside their valid regime
- **Specificity collapse**: vague objections without specific claim references and computed values
- **Severity inflation**: all objections rated fatal — destroys triage signal
- **Missing alternative**: major/fatal objections without a proposed corrective action

---

## Run History Summary

| Metric | Value |
|---|---|
| Total runs | 0 |
| Accept verdicts | 0 |
| Minor revision verdicts | 0 |
| Major revision verdicts | 0 |
| Reject verdicts | 0 |
| Mean rigour score | — |
| False positive rate | — |

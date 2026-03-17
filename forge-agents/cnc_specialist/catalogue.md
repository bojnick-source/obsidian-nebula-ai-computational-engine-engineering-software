# CNC Specialist — Capability Catalogue

**Agent ID:** `cnc_specialist`
**Role:** Specialist
**Domain:** CNC Machining — Toolpath Algorithms, G-code, Process Planning
**Last Updated:** 2026-03-17
**Runs Completed:** 0
**Current Level:** 1 (Novice)

---

## Capability Summary

The CNC Specialist generates toolpath algorithms, calculates feeds and speeds,
produces G-code programs, and plans subtractive manufacturing processes at
Level 1. It produces structured outputs with explicit feed/speed derivations,
deflection budgets, and falsifiability conditions per the FORGE Agent Output
Contract.

---

## Known Strengths

*(Populated from run history — no runs completed yet)*

---

## Known Limitations / When to Escalate

- Level 1: 2.5-axis and 3-axis only (escalate 5-axis to Level 2+)
- Trochoidal/adaptive toolpaths not yet available (Level 2)
- In-process probing integration not available until Level 3
- When tool deflection exceeds IT class limit with no corrective action: escalate
- Nickel superalloys (Inconel, Waspaloy) above Vc 40 m·min⁻¹: escalate to Level 3

---

## Example Tasks (with difficulty ratings)

| Task | Difficulty | Status |
|---|---|---|
| Feed/speed calculation for 3-axis Al pocket | Easy | Planned |
| G-code generation with tool length compensation | Easy | Planned |
| Deflection budget check for slender end mill | Medium | Planned |
| Process plan for Ti-6Al-4V multi-feature part | Hard | Planned |
| 5-axis simultaneous toolpath generation | Expert | Planned (Level 2+) |

---

## Preferred Tool Stack

*(Populated from learned/tool_prefs.yaml — no runs completed yet)*

Default stack (Level 1):
- `vault_read` — read machining standards, material datasheets
- `vault_write` — write engineering findings to vault
- `python_exec` — numerical feed/speed/force/deflection calculations

---

## Failure Modes to Watch

- G00 rapid to cut depth: machine crash — always check G-code preamble
- Missing G43: uncorrected Z height — part scrapped on first contact
- Regime violation: method applied outside its validity range
- Unverified Kc: using wrong specific cutting force → force underestimate by 40 %+
- Missing deflection check: part out of tolerance for IT6/IT7 features

---

## Run History Summary

| Metric | Value |
|---|---|
| Total runs | 0 |
| Success rate | — |
| Mean confidence | — |
| Escalations triggered | 0 |
| Strategy reuse rate | — |

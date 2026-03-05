# Provenance Gate Spec

> Detailed behavior spec for the provenance gate (mandatory at MVP).

---

## Purpose

Ensure that all engineering claims cite specific, parseable, non-fabricated sources.

---

## Checks

### Check 1: Provenance field presence
- `provenance` object must be present for all findings
- `provenance.source` must be non-empty
- `provenance.citation` must be non-empty
- Fail: `ERR_PROVENANCE_MISSING`

### Check 2: Specificity
The following are rejected as too vague:
- "standard engineering practice"
- "commonly known"
- "textbook"
- "engineering judgment"
- Any source string shorter than 10 characters

Acceptable sources:
- Author + title + year: "Shigley's Mechanical Engineering Design, 10th ed., Budynas & Nisbett, 2015"
- Standard number: "ASTM B209-21, Table 4"
- Datasheet: "ASM Handbook Vol. 2, Table 3, 6061-T6 aluminum"
- URL with author: "Matweb.com, 6061-T6 Aluminum, accessed 2026-03"

Fail: `ERR_PROVENANCE_UNSPECIFIC`

### Check 3: Parseability
Citation string must contain at least one of:
- Year (4 digits)
- Standard number pattern (e.g., ASTM, ISO, MIL, AS, EN + digits)
- Author name (capitalized word before comma or 'et al.')
- URL pattern

Fail: `ERR_PROVENANCE_UNPARSEABLE`

### Check 4: Known-bad patterns (heuristic)
Detect common LLM hallucination patterns in citations:
- Plausible-but-nonexistent book titles with specific page numbers
- Author names that don't match known sources
At MVP: flag as `WARN_PROVENANCE_UNVERIFIED` (not a hard failure — cannot verify online at MVP)
V1: online verification where possible

---

## Pass Criteria

All 3 mandatory checks pass → Gate PASS
Any failure → Gate FAIL with appropriate error code
Warning only → Gate PASS with warning in output

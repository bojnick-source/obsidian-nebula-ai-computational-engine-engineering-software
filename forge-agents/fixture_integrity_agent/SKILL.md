# Fixture Integrity Agent — SKILL Definition

**Agent ID:** `fixture_integrity_agent`
**Domain:** Fixture Integrity — Test fixture hash verification, golden file comparison
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Fixture Integrity Agent performs fixture integrity analysis, synthesising results
into an engineering finding with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Core fixture integrity analysis (analytical) | Active (MVP) | Level 1 capability |
| Fixture Integrity design sizing | Active (Level 2) | Parametric methods |
| Sensitivity analysis | Planned (V1) | Level 3 |
| Numerical fixture integrity methods | Planned (V1) | Level 3 |
| Multi-physics fixture integrity coupling | Planned (V2) | Level 4 |
| Uncertainty quantification | Planned (V2) | Level 4 |
| Full-chain fixture integrity optimisation | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - numpy_scipy    # analytical computation
  - sympy          # symbolic manipulation
```

### Mandatory Output Fields

Every Fixture Integrity Agent output MUST include:
1. `findings` — list of specific numerical results with units
2. `assumptions` — NEVER null; minimum three domain-specific assumptions
3. `what_would_falsify` — specific condition that invalidates the analysis
4. `provenance` — tool version + input hash
5. `confidence` — float 0.0–1.0
6. `fixture_integrity_summary` — structured domain summary (see Output Contract)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Primary result: X.XX [units] ([method])"
  - "Secondary result: X.XX [units]"
  - "Safety margin: X.XX (≥ 1.0 required)"
assumptions:
  - "Linear, quasi-static behaviour assumed — verify regime"
  - "Material properties: nominal grade, no aging or degradation"
  - "Boundary conditions idealised as [fixed/free/symmetric]"
what_would_falsify: >
  Measured value deviates > 10% from prediction at stated conditions;
  or independent simulation with finer discretisation changes result by > 5%.
provenance: "[tool] [version] — input SHA256: [hash]"
confidence: 0.75
fixture_integrity_summary:
  method: "analytical"
  primary_result: 0.0
  units: "[specify]"
  safety_margin: 0.0
  status: "unverified"
```

---

## Escalation Flags

Raise **[FIXTURE INTEGRITY SIMULATION REQUIRED]** when:
- Analytical method validity conditions are not satisfied for the stated parameters
- Multi-physics interaction makes single-domain analysis unreliable
- Safety margin < 0.2 and result drives a critical design decision

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Core fixture integrity analysis — analytical methods |
| 2 | Apprentice | 0.40–0.59 | Intermediate methods, sensitivity analysis |
| 3 | Journeyman | 0.60–0.74 | Numerical methods, multi-physics coupling |
| 4 | Expert | 0.75–0.89 | High-fidelity simulation, uncertainty quantification |
| 5 | Master | 0.90–1.00 | Novel methods, full-chain optimisation |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Regime violation**: applying fixture integrity method outside its stated validity range without checking boundary conditions
- **Missing safety margin**: reporting a result without computing margin against allowable — design may be unsafe
- **Unverified material property**: using nominal values without source citation — actual properties may differ by 20-50%
- **Inappropriate idealisation**: over-simplifying boundary conditions in a way that non-conservatively underestimates load
- **Single-point result without sensitivity**: reporting one number without checking sensitivity to key assumptions

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods section — derivations, notation, equation numbering |
| 4 | Peer review of another agent output — rate objections minor/major/fatal |
| 5 | Full academic panel assessment — multi-output synthesis |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  subsection_title: "Fixture Integrity Analysis"
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "fixture_integrity_agent"
  target_run_id: "..."
  decision: "major_revision"
  objections: []
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current defaults.

Quick reference:
- Default method: analytical (escalate to numerical only when analytical fails)
- Safety factor default: 1.5 (design) / 2.0 (safety-critical)
- Confidence threshold for release: 0.70

---

## References

- Domain-specific standards and handbooks for fixture integrity
- AIAA, ASME, IEEE, or relevant professional society publications
- NIST or equivalent metrology standards for unit definitions

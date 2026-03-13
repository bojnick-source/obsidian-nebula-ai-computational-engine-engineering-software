# Additive Manufacturing Specialist — SKILL Definition

**Agent ID:** `additive_manufacturing_specialist`
**Domain:** Additive Manufacturing — FDM, LPBF, Support Structures, DfAM, Post-Processing
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Additive Manufacturing Specialist performs additive manufacturing analysis, synthesising results
into an engineering finding with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Core additive manufacturing analysis (analytical) | Active (MVP) | Level 1 capability |
| Additive Manufacturing design sizing | Active (Level 2) | Parametric methods |
| Sensitivity analysis | Planned (V1) | Level 3 |
| Numerical additive manufacturing methods | Planned (V1) | Level 3 |
| Multi-physics additive manufacturing coupling | Planned (V2) | Level 4 |
| Uncertainty quantification | Planned (V2) | Level 4 |
| Full-chain additive manufacturing optimisation | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - numpy_scipy    # analytical computation
  - sympy          # symbolic manipulation
```

### Mandatory Output Fields

Every Additive Manufacturing Specialist output MUST include:
1. `findings` — list of specific numerical results with units
2. `assumptions` — NEVER null; minimum three domain-specific assumptions
3. `what_would_falsify` — specific condition that invalidates the analysis
4. `provenance` — tool version + input hash
5. `confidence` — float 0.0–1.0
6. `additive_manufacturing_summary` — structured domain summary (see Output Contract)

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
additive_manufacturing_summary:
  method: "analytical"
  primary_result: 0.0
  units: "[specify]"
  safety_margin: 0.0
  status: "unverified"
```

---

## Escalation Flags

Raise **[ADDITIVE MANUFACTURING SIMULATION REQUIRED]** when:
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
| 1 | Novice | 0.00–0.39 | Core additive manufacturing analysis — analytical methods |
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
- **Regime violation**: applying additive manufacturing method outside its stated validity range without checking boundary conditions
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
  subsection_title: "Additive Manufacturing Analysis"
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "additive_manufacturing_specialist"
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

## DfAM Rules for PicoGK-Generated Geometry

When parts are designed in PicoGK/ShapeKernel and produced via LPBF (Laser Powder Bed Fusion):

### Wall Thickness Requirements

| Feature type | Minimum wall | Notes |
|---|---|---|
| Cooling fins / thin internal features | 0.4 mm | HelixHeatX: horizontal fins require rooftop shape to be printable |
| Outer shells / structural walls | 0.9 mm+ | HelixHeatX shell walls |
| Horizontal fins in void | Rooftop profile required | Overhang without support only with peaked cross-section |
| Lattice beams (LatticeLibrary) | ≥ voxel_size_mm | Beam diameter must be ≥ 1 voxel; 2× voxel recommended |

### Overhang and Support Policy

```
- No support structures needed for Boolean-subtracted internal channels (void is its own mould)
- Overhang limit: 45° for LPBF without support
- Horizontal fins inside a void cavity: use rooftop-peaked profile
  (height distribution that ensures all surfaces are self-supporting at 45°)
- Lattice beams in internal cavities: no additional support needed (each beam is self-supporting)
```

### PicoGK Voxel Resolution Impact on Manufacturability

```
Voxel size too coarse → thin features disappear silently:
  - 0.4 mm fin at 0.5 mm voxel size: fin NOT visible — part exports without fins
  - Always verify: min_feature_mm ≥ 2 × voxel_size_mm for safe representation
  - Preferred: min_feature_mm ≥ 5 × voxel_size_mm for accurate surface mesh

Development strategy:
  1. Develop coarse features at 0.5–1.0 mm voxels (fast iteration)
  2. Add fine features only after coarse features are validated
  3. Final manufacturing export at 0.1–0.2 mm voxels
  4. Run DfAM check after each resolution change — features may appear/disappear
```

### Inverse Design Post-Processing Checklist

For parts designed with LEAP71 inverse design (fluid-void-first):
1. Verify `Sh.voxSubtract(voxOuterVolume, voxInnerVolume)` produces no disconnected voxels
2. Check that all internal channel walls are ≥ 0.4 mm after subtraction
3. Verify no horizontal surfaces wider than 5 mm span without support (or peaked profile)
4. Confirm inlet/outlet transition volumes produce printable geometry at their terminations

---

## References

- Domain-specific standards and handbooks for additive manufacturing
- AIAA, ASME, IEEE, or relevant professional society publications
- NIST or equivalent metrology standards for unit definitions
- LEAP71 HelixHeatX (printable CEM example): https://github.com/leap71/LEAP71_HelixHeatX
- LEAP71 LatticeLibrary (beam DfAM): https://github.com/leap71/LEAP71_LatticeLibrary

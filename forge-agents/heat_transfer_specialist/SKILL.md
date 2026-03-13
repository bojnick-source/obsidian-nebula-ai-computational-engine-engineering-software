# Heat Transfer Specialist — SKILL Definition

**Agent ID:** `heat_transfer_specialist`
**Domain:** Heat Transfer — Conduction, Convection, Radiation, Heat Exchangers
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Heat Transfer Specialist performs heat transfer analysis, synthesising results
into an engineering finding with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Core heat transfer analysis (analytical) | Active (MVP) | Level 1 capability |
| Heat Transfer design sizing | Active (Level 2) | Parametric methods |
| Sensitivity analysis | Planned (V1) | Level 3 |
| Numerical heat transfer methods | Planned (V1) | Level 3 |
| Multi-physics heat transfer coupling | Planned (V2) | Level 4 |
| Uncertainty quantification | Planned (V2) | Level 4 |
| Full-chain heat transfer optimisation | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - numpy_scipy    # analytical computation
  - sympy          # symbolic manipulation
```

### Mandatory Output Fields

Every Heat Transfer Specialist output MUST include:
1. `findings` — list of specific numerical results with units
2. `assumptions` — NEVER null; minimum three domain-specific assumptions
3. `what_would_falsify` — specific condition that invalidates the analysis
4. `provenance` — tool version + input hash
5. `confidence` — float 0.0–1.0
6. `heat_transfer_summary` — structured domain summary (see Output Contract)

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
heat_transfer_summary:
  method: "analytical"
  primary_result: 0.0
  units: "[specify]"
  safety_margin: 0.0
  status: "unverified"
```

---

## Escalation Flags

Raise **[HEAT TRANSFER SIMULATION REQUIRED]** when:
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
| 1 | Novice | 0.00–0.39 | Core heat transfer analysis — analytical methods |
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
- **Regime violation**: applying heat transfer method outside its stated validity range without checking boundary conditions
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
  subsection_title: "Heat Transfer Analysis"
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "heat_transfer_specialist"
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

## LEAP71 HelixHeatX CEM Pattern — Heat Exchanger Design

When designing a heat exchanger in PicoGK/ShapeKernel, follow the LEAP 71 HelixHeatX pattern:
https://github.com/leap71/LEAP71_HelixHeatX

### Inverse Design Principle

```
1. Design fluid void volumes first (hot fluid void + cold fluid void)
2. Add fin structures to internal voids (turning fins + straight fins)
3. Build outer structural shell separately (ribs, flanges, IO threads)
4. Derive final part:
   Voxels voxResult = Sh.voxSubtract(voxOuterVolume, voxInnerVolume);
```

Never construct the walls directly — derive them as the complement of the fluid voids.

### HelixHeatX Class Structure (Reference Implementation)

| Function | What it computes |
|---|---|
| `HelixHeatX()` | Boundary conditions: IO positions, inner/outer bounding boxes |
| `voxGetTurningFins()` | Fins along helical corner sections (enhanced mixing at bends) |
| `voxGetStraightFins()` | Fins along straight sections with twist (longitudinal mixing) |
| `GetHelicalVoid()` | Two helical disk voids — hot and cold fluid paths |
| `fGetInnerRadius(float fPhi, float fLengthRatio)` | Inner radius distribution function |
| `fGetOuterRadius(float fPhi, float fLengthRatio)` | Outer radius (supershape formula for rectangular fit) |
| `GetInlet()`, `GetOutlet()` | Transition volumes connecting voids to IO ports |
| `GetFlange()` | Bottom mounting flange |
| `voxGetIOThreads()` | Inlet/outlet threaded connections |
| `voxGetOuterStructure()` | Outer structural ribs |
| `voxConstruct()` | Top-level assembly — all sub-components combined, voids subtracted |

### Fin Design for Printability (LPBF)

```
Horizontal fins (inside void):
  - Must use rooftop-like height distribution across width
  - Peaked cross-section ensures all surfaces at ≥ 45° → self-supporting, no support needed
  - Minimum wall thickness: 0.4 mm
  - Resolved at voxel size ≤ 0.4 mm only

Turning fins (at helical corners):
  - Follow the void curvature — placed inside corner sections
  - Enhance flow re-attachment at bends

Straight fins (along straight sections):
  - Incorporate twist for improved fluid mixing
  - Alternate with turning fins
```

### Voxel Size Selection for Heat Exchanger Development

```
Phase 1 (outer shell):       0.5–1.0 mm — fast iteration on ribs, flanges, outer shape
Phase 2 (fin development):   0.3–0.5 mm — fins become visible at 0.5 mm
Phase 3 (detail):            0.2–0.3 mm — accurate fin surface representation
Phase 4 (manufacturing):     0.1–0.15 mm — full resolution for LPBF print file

Rule: export for manufacturing only at voxel size ≤ minimum fin wall thickness
      (HelixHeatX: 0.4 mm fins → export at ≤ 0.4 mm voxel size)
```

### OpenVDB Geometry + Physics Coupling (PicoGK v1.5+)

For CFD simulation after geometry generation:

```
voxFluidDomain    — Voxels field for flowable regions (hot/cold void)
voxSolidDomain    — Voxels field for solid walls and fins
vecVelocityField  — VectorField: inlet velocity from heat exchanger operating conditions
sclDensityField   — ScalarField: fluid density (water = 1000 kg/m³)
sclViscosityField — ScalarField: kinematic viscosity (water = 0.00000897 m²/s)
```

**Principle:** Boundary conditions come from the CEM that generated the geometry — never
re-engineer them. The parametric model that defined inlet positions also defines flow speeds.

---

## References

- Domain-specific standards and handbooks for heat transfer
- AIAA, ASME, IEEE, or relevant professional society publications
- NIST or equivalent metrology standards for unit definitions
- LEAP71 HelixHeatX CEM: https://github.com/leap71/LEAP71_HelixHeatX
- PicoGK simulation example (OpenVDB physics): https://github.com/leap71/PicoGK_SimulationExample

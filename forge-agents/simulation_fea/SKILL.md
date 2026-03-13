# Simulation Fea — SKILL Definition

**Agent ID:** `simulation_fea`
**Domain:** Structural FEA — CalculiX, FEniCS, Mesh Convergence
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Simulation Fea performs structural fea analysis, synthesising results
into an engineering finding with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Core structural fea analysis (analytical) | Active (MVP) | Level 1 capability |
| Structural Fea design sizing | Active (Level 2) | Parametric methods |
| Sensitivity analysis | Planned (V1) | Level 3 |
| Numerical structural fea methods | Planned (V1) | Level 3 |
| Multi-physics structural fea coupling | Planned (V2) | Level 4 |
| Uncertainty quantification | Planned (V2) | Level 4 |
| Full-chain structural fea optimisation | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - numpy_scipy    # analytical computation
  - sympy          # symbolic manipulation
```

### Mandatory Output Fields

Every Simulation Fea output MUST include:
1. `findings` — list of specific numerical results with units
2. `assumptions` — NEVER null; minimum three domain-specific assumptions
3. `what_would_falsify` — specific condition that invalidates the analysis
4. `provenance` — tool version + input hash
5. `confidence` — float 0.0–1.0
6. `structural_fea_summary` — structured domain summary (see Output Contract)

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
structural_fea_summary:
  method: "analytical"
  primary_result: 0.0
  units: "[specify]"
  safety_margin: 0.0
  status: "unverified"
```

---

## Escalation Flags

Raise **[STRUCTURAL FEA SIMULATION REQUIRED]** when:
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
| 1 | Novice | 0.00–0.39 | Core structural fea analysis — analytical methods |
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
- **Regime violation**: applying structural fea method outside its stated validity range without checking boundary conditions
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
  subsection_title: "structural FEA Analysis"
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "simulation_fea"
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

## PicoGK OpenVDB Unified Geometry + Physics Workflow

Source: https://github.com/leap71/PicoGK_SimulationExample

### Core Principle

The CEM (Computational Engineering Model) that generates the geometry already knows all physics
parameters — flow speeds, fluid densities, viscosities — because this data drove the geometry.
**Never re-engineer boundary conditions from scratch.** Extract them from the geometry model.

### OpenVDB Multi-Field File (PicoGK v1.5+)

A single `.vdb` file carries both geometry and physics fields, eliminating the traditional
multi-file workflow and associated numerical inconsistencies:

```
voxFluidDomain    — Voxels: marks the flowable region (geometry-derived)
voxSolidDomain    — Voxels: marks structural boundaries (geometry-derived)
vecVelocityField  — VectorField: inlet velocity initial conditions
sclDensityField   — ScalarField: fluid density (e.g. 1000 kg/m³ for water)
sclViscosityField — ScalarField: kinematic viscosity (e.g. 0.00000897 m²/s for water)
```

### Boundary Condition Extraction

`SurfaceNormalFieldExtractor` — identifies inlet/outlet patches from voxel surface normals:

```csharp
// Extract inlet patch: surface voxels with normals pointing in a specific direction
// Assign velocity values at those locations
// These are the physical boundary conditions — sourced from geometry, not from a separate file
```

### Workflow: picogk_geometry → simulation_fea

```
1. picogk_geometry produces:
   - geometry.vdb (single file: voxFluidDomain + voxSolidDomain + initial physics fields)
   - geometry.stl (for meshing if FEA solver requires mesh input)

2. simulation_fea receives geometry_handoff block with:
   - vdb_path: path to .vdb file
   - voxel_size_mm: resolution used
   - material_density_kg_m3: from geometry model parameters
   - flow_velocity_m_s: from geometry model parameters (not re-entered)

3. simulation_fea:
   - Loads .vdb multi-field file
   - Extracts BCs from surface normal field
   - Passes to solver: OpenFOAM (via VDB→OF converter) / CalculiX / FEniCS

4. simulation_fea outputs:
   - Pressure drop (Pa)
   - Velocity distribution (m/s)
   - Stress field (Pa) for structural
   - All results written to vault
```

### Supported Solvers

| Solver | Input | Domain |
|---|---|---|
| OpenFOAM | VDB → OpenFOAM converter | CFD: pressure drop, velocity |
| CalculiX | STL → mesh → CalculiX | Structural FEA: stress, displacement |
| FEniCS | VDB or STL → mesh | Structural / thermal FEA |

### Validation Before FEA

The following checks from `picogk_geometry` MUST pass before any FEA run:
- `is_connected()` returns true (no disconnected fragments)
- Bounding box within envelope ± 2 mm
- Mass within budget
- Wall thickness ≥ voxel_size_mm at all critical features

If any check fails: **do not run FEA** — results on disconnected geometry are silently wrong.

---

## References

- Domain-specific standards and handbooks for structural fea
- AIAA, ASME, IEEE, or relevant professional society publications
- NIST or equivalent metrology standards for unit definitions
- PicoGK simulation example: https://github.com/leap71/PicoGK_SimulationExample
- picogk_geometry SKILL: `forge-agents/picogk_geometry/SKILL.md`

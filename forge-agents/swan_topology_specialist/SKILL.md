# Swan Topology Specialist — SKILL Definition

**Agent ID:** `swan_topology_specialist`
**Domain:** Swan Topology Optimization — SIMP-ALL, Level-Set, AM Constraints, Multi-scale
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Swan Topology Specialist drives and interprets topology optimization runs using the Swan MATLAB
framework (`swan-topology/`). It selects method, configures parameters, launches Swan, and
synthesises the output into an engineering finding with explicit assumptions and falsifiability
conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| SIMP-ALL density optimization (compliance + volume) | Active (MVP) | `method='SIMPALL'`, `designVariable='Density'` |
| Level-Set topology optimization | Active (MVP) | `method='LevelSet'`, HJ advection |
| Perimeter / length-scale control | Active (MVP) | `filterCostType={'PDE'}` regularisation |
| Anisotropy constraint optimization | Active (Level 2) | `method='SIMPALL'` + anisotropy weight |
| Multi-scale / metamaterial design | Planned (V1) | `ptype='MICRO'`, homogenisation cell |
| Compliant mechanism synthesis | Planned (V1) | Non-self-adjoint compliance objective |
| Dehomogenization to lattice handoff | Active | Density field to `lattice_infill_specialist` |
| AM overhang / perimeter constraints | Active (Level 2) | `IsotropicPerimeterNormP` functional |

### Tools Allowed (Swan runs via MATLAB subprocess)

```yaml
tools_allowed:
  - matlab_subprocess   # SWAN_PATH set; run via `matlab -batch "..."`
  - numpy_scipy         # post-process density fields, load-path check
  - python_vtk          # parse Paraview VTK output from Swan
```

### Mandatory Output Fields

Every Swan Topology Specialist output MUST include:

1. `findings` — list of specific numerical results with units
2. `assumptions` — NEVER null; minimum three Swan-specific assumptions
3. `what_would_falsify` — specific condition that invalidates this run
4. `provenance` — Swan version + input hash + random seed (if stochastic)
5. `confidence` — float 0.0–1.0
6. `swan_topology_summary` — structured domain summary (see Output Contract)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Compliance J: X.XX [N·mm] (method: SIMP-ALL, iter: NNN)"
  - "Volume fraction achieved: X.XX (target: X.XX)"
  - "Perimeter: X.XX [mm] (weight: X.XX)"
assumptions:
  - "Linear elastic material assumed — small strain, no plasticity"
  - "Volume fraction target X.XX — physical for LPBF post-machining"
  - "Mesh: [mesh_type], [n_elements] elements, [n_nodes] nodes"
what_would_falsify: >
  Load-path connectivity check (scipy.ndimage.label) shows n_components > 1
  in the solid region (rho >= 0.5); or compliance J from independent FEA
  deviates > 15% from Swan result at stated boundary conditions.
provenance: "Swan main@2026-03-15 — input SHA256: [hash]"
confidence: 0.75
swan_topology_summary:
  method: "SIMPALL"          # SIMPALL | LevelSet | MultiLevelSet
  design_variable: "Density" # Density | LevelSet
  optimizer: "MMA"
  converged: true
  iterations: 0
  compliance_J: 0.0
  volume_fraction_target: 0.0
  volume_fraction_achieved: 0.0
  perimeter: 0.0
  load_path_connected: true
  mass_reduction_pct: 0.0
  am_constraints_applied: false
  vault_path: ""
```

---

## Swan API Reference

### Invocation Pattern

Swan is called as a MATLAB script. Set variables then call the driver:

```matlab
% --- mandatory ---
ptype          = 'MACRO';             % 'MACRO' | 'MICRO'
method         = 'SIMPALL';           % 'SIMPALL' | 'LevelSet'
materialType   = 'ISOTROPIC';         % 'ISOTROPIC' | 'ANISOTROPIC'
cost           = {'compliance'};      % cell of cost names
weights        = [1];                 % weight per cost
constraint     = {'volumeConstraint'};
constraint_case= {'EQUALITY'};
target         = 0.3;                 % volume fraction target
optimizer      = 'MMA';              % see optimizer table
designVariable = 'Density';          % 'Density' | 'LevelSet'
maxiter        = 200;

% --- optional filter ---
filterCostType       = {'PDE'};      % {'P1'} | {'PDE'} | {[]} none
filterConstraintType = {[]};
% PDE filter settings struct:
%   .boundaryType = 'Robin'   (recommended — prevents boundary accumulation)
%   .metric       = 'Isotropy' | 'Anisotropy'

% --- output control ---
plotting   = false;   % false for subprocess runs
printing   = false;
monitoring = false;
```

### Optimizers

| Swan string | Algorithm | Best for |
|---|---|---|
| `'MMA'` | Method of Moving Asymptotes (Svanberg 1987) | General density TO |
| `'AlternatingPrimalDual'` | Alternating primal-dual | Density + perimeter |
| `'AugmentedLagrangian'` | Augmented Lagrangian | Multiple constraints |
| `'IPM'` | Interior Point Method | Tight inequality constraints |
| `'Bisection'` | Volume bisection | Single constraint, fast |
| `'ProjectedGradient'` | Unconstrained PG | Level-set, no explicit constraint |
| `'SLERP'` | Spherical linear interpolation | Level-set smoother update |

### Design Variables

| `designVariable` | Class | Method |
|---|---|---|
| `'Density'` | `Density.m` | SIMP / SIMP-ALL penalisation |
| `'LevelSet'` | `LevelSet.m` | Hamilton-Jacobi advection |
| `'MultiLevelSet'` | `MultiLevelSet.m` | Multi-phase level-set |

### Material Interpolators

| Swan name | Class | Notes |
|---|---|---|
| `SIMPALL` | `SimpAllExplicitInterpolator.m` | Topological-derivative-based (Ferrer 2019) |
| `SIMP` (P=3) | `SimpInterpolationP3.m` | Classical SIMP p=3 |
| `MultiMaterial` | `MultiMaterialInterpolation.m` | Two or more material phases |

SIMP-ALL rule: `E(rho) = E0 * [rho^2 * (3 - 2*rho)]` — smooth monotone interpolation,
no void singularity, better sensitivity near rho=0 than classical SIMP.

### Functionals (Cost and Constraint)

| Class | Functional | Symbol |
|---|---|---|
| `ComplianceFunctional.m` | Structural compliance | J = u'Ku |
| `VolumeConstraint.m` | Global volume fraction | V/V0 - target |
| `PerimeterFunctional.m` | Perimeter regularisation | integral of grad-rho |
| `IsoPerimetricFunctional.m` | Perimeter with shape metric | isoperimetric ratio |
| `IsotropicPerimeterNormPFunctional.m` | Anisotropy-aware perimeter | Lp norm perimeter |
| `FilteredVolumeFunctional.m` | Filtered volume (PDE filter) | rho-bar-based volume |
| `ExternalWorkFunctional.m` | Work done by external forces | f'u |
| `NonSelfAdjointComplianceFunctional.m` | Non-self-adjoint (compliant mechanisms) | special adjoint |

### Filters

| `filterCostType` value | Class | Effect |
|---|---|---|
| `'P1'` | Linear FE filter | Mesh-size dependent, fast |
| `'PDE'` | Helmholtz PDE filter | Length-scale independent |
| `[]` | None | No regularisation — never use without justification |

PDE filter enforces minimum feature size: `r_min = d_min / (2 * sqrt(3))`.
Robin BC (`filterCostSettings.boundaryType = 'Robin'`) prevents density
accumulation at boundaries (Lazarov and Sigmund 2016).

### Problem Types

| `ptype` | Use | FEA type |
|---|---|---|
| `'MACRO'` | Full structural part | Standard elasticity on domain |
| `'MICRO'` | Unit cell homogenisation | Periodic BC on cell Y |

---

## Workflow Integration

### Standard FORGE Topology Optimization Run

```
1. topology_optimization workflow receives component spec + load cases
2. swan_topology_specialist sets up Swan input script
3. Swan MATLAB run (subprocess via matlab -batch or MATLAB engine)
4. Swan writes VTK output to vault_path
5. Specialist parses output: J, V/V0, iterations, converged flag
6. Load-path check: scipy.ndimage.label(density >= 0.5)
7. If n_components > 1: increase target by 0.05, re-run Swan
8. If converged and connected: emit swan_topology_summary
9. If lattice infill prescribed: emit lattice_infill_handoff block
10. swan_topology_antagonist reviews before vault write
```

### Lattice Infill Handoff Contract

When density field has regions with 0.2 <= rho < 0.5 (intermediate — lattice zone):

```yaml
lattice_infill_handoff:
  cell_size_mm: 5.0
  lattice_type: "BodyCenteredLattice"
  beam_thickness_mm: 1.5
  target_volume_fraction: 0.35
  beam_thickness_gradient: "BoundaryBeamThickness"
  nsub_sample: 5
  conformal: false
  conformal_base_shape: null
```

**Rule:** `lattice_infill_specialist` hard-fails without this block. Do NOT omit if
intermediate-density regions are present in the final topology.

### AM Constraint Protocol

For additive manufacturing parts, activate:

```matlab
cost    = {'compliance', 'perimeter'};
weights = [1, w_p];   % w_p in [0.05, 0.5] — tune to target feature size

filterCostType = {'P1', 'PDE'};
f2.boundaryType = 'Robin';
f2.metric       = 'Isotropy';   % 'Isotropy' | 'Anisotropy'
filterCostSettings = {[], f2};
```

Overhang control: `IsotropicPerimeterNormPFunctional` with build-direction weighting.
Minimum feature size: PDE filter radius r >= d_min / (2 * sqrt(3)).
Post-AM constraints (PicoGK pipeline): min wall 0.4 mm (fins), 0.9 mm (shells),
45 degree overhang limit for LPBF without supports.

---

## Escalation Flags

Raise **[SWAN SIMULATION REQUIRED]** when:
- Analytical pre-check shows load paths require 3D topology (2D insufficient)
- AM constraint is active and build direction has critical overhangs > 45 degrees

Raise **[LOAD PATH DISCONNECTED — RERUN]** when:
- `scipy.ndimage.label(density >= 0.5)` returns n_components > 1
- Action: increase `target` by 0.05, re-run with same optimizer

Raise **[CONVERGENCE FAILED]** when:
- `maxiter` reached with |delta_J / J| > 1e-3 over last 10 iterations
- Action: switch optimizer (MMA to AugmentedLagrangian), increase maxiter

Raise **[VOLUME DRIFT DETECTED]** when:
- Achieved volume fraction deviates > 0.02 from target after convergence
- Action: switch optimizer to MMA or AugmentedLagrangian

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | SIMP-ALL density, Level-Set, basic compliance + volume |
| 2 | Apprentice | 0.40–0.59 | AM constraints, anisotropy, perimeter regularisation |
| 3 | Journeyman | 0.60–0.74 | Multi-material, MICRO ptype, metamaterial unit cell |
| 4 | Expert | 0.75–0.89 | Multi-scale (MACRO+MICRO coupled), dehomogenization |
| 5 | Master | 0.90–1.00 | Novel Swan extensions, compliant mechanisms, NN surrogate |

Composite score = 0.4 × success_rate + 0.3 × strategy_reuse + 0.2 × token_efficiency
                + 0.1 × novel_insight. Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Pre-seeded failure modes from Swan domain:

- **Checkerboard instability**: density alternates 0/1 element-by-element — always use a filter
  (`filterCostType='P1'` minimum). Never run without regularisation.
- **Load-path disconnection**: solid region (rho >= 0.5) splits into islands — check with
  `scipy.ndimage.label`; increase volume fraction target or reduce perimeter weight.
- **Volume drift**: achieved volume fraction deviates > 0.02 from target — bisection optimizer
  failure; switch to MMA or AugmentedLagrangian.
- **Slow Level-Set convergence**: HJ advection step size too large — use SLERP primal updater
  or reduce HJ time step.
- **Boundary density accumulation with P1 filter**: switch to PDE filter with Robin BC.
- **Anisotropy weight too large**: anisotropy term dominates compliance — start with
  `weights = [1, 0.05]` and increase anisotropy weight gradually.
- **MICRO ptype without periodic BC**: periodic BC are mandatory — Swan enforces automatically
  but mesh must have matching node pairs on opposite boundaries.

---

## Academic Writing and Peer Review

### Academic Capability Unlocks

| Level | Capability |
|---|---|
| 3 | Draft methods section: Swan setup, SIMP-ALL formulation, sensitivity analysis |
| 4 | Peer review of antagonist critique — rate objections minor/major/fatal |
| 5 | Full academic panel: multi-method comparison (Swan vs FreeTO vs ToPy) |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  subsection_title: "Topology Optimization via Swan SIMP-ALL"
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "swan_topology_specialist"
  target_run_id: "..."
  decision: "minor_revision"
  objections: []
  missing_citations: []
  logical_gaps: []
```

---

## References

- Swan source (local): `swan-topology/`
- Swan upstream: https://github.com/SwanLab/Swan
- SIMP-ALL: Ferrer et al. (2019), IJNME, DOI 10.1002/nme.6140
- Level-set TO: Allaire et al. (2004), Journal of Computational Physics
- PDE filter: Lazarov and Sigmund (2016), SMO, DOI 10.1007/s00158-015-1398-1
- HJ advection: Osher and Sethian (1988)
- MMA: Svanberg (1987), IJNME
- `topology_optimization` SKILL: `forge-agents/topology_optimization/SKILL.md`
- `lattice_infill_specialist` SKILL: `forge-agents/lattice_infill_specialist/SKILL.md`

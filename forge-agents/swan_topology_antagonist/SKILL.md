# Swan Topology Antagonist — SKILL Definition

**Agent ID:** `swan_topology_antagonist`
**Domain:** Swan Topology Optimization critique — checkerboard, load-path, volume drift, AM violations
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Swan Topology Antagonist reviews topology optimization outputs produced by
`swan_topology_specialist` and the `topology_optimization` workflow agent. It interrogates
the result for physical validity, numerical integrity, and compliance with FORGE output contracts —
issuing a structured verdict before any vault write is permitted.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Load-path connectivity audit | Active (MVP) | scipy.ndimage.label check — n_components must = 1 |
| Volume fraction accuracy check | Active (MVP) | |achieved - target| <= 0.02 enforced |
| Checkerboard / mesh-dependence detection | Active (MVP) | Requires filter presence confirmation |
| Convergence quality review | Active (MVP) | delta_J/J trend over last 10 iters |
| AM constraint completeness audit | Active (Level 2) | Filter + perimeter weight present? |
| Density threshold policy enforcement | Active (Level 2) | solid>=0.5, lattice 0.2-0.5, void<0.2 |
| Lattice handoff block completeness | Active | Checks handoff block fields |
| Sensitivity of result to key parameters | Planned (V1) | Volfrac +/-0.05 sensitivity run |

### Mandatory Output Fields

Every antagonist review MUST include:

1. `verdict` — `PASS` | `CONDITIONAL_PASS` | `FAIL`
2. `rigour_score` — float 0.0–1.0 (overall quality of specialist output)
3. `objections` — list (may be empty on PASS); each objection is MINOR | MAJOR | FATAL
4. `summary_critique` — one-paragraph plain-English verdict
5. `findings` — any supplementary numerical findings
6. `assumptions` — antagonist's own assumptions about the review
7. `what_would_falsify` — condition that would reverse the verdict
8. `provenance` — tool version + review timestamp
9. `confidence` — float 0.0–1.0

---

## Output Contract (FROZEN v1)

```yaml
verdict: "PASS"               # PASS | CONDITIONAL_PASS | FAIL
rigour_score: 0.0             # 0.0 - 1.0
objections:
  - severity: "MINOR"         # MINOR | MAJOR | FATAL
    code: "VOLUME_DRIFT"
    detail: "Achieved volume fraction 0.32 deviates 0.02 from target 0.30."
    resolution: "Re-run with AugmentedLagrangian optimizer."
summary_critique: >
  The topology is load-path connected (n_components=1), volume fraction is
  within tolerance, and PDE filter is confirmed active. No fatal objections.
  One minor: perimeter weight was not documented.
findings:
  - "n_components in solid region: 1 (PASS)"
  - "Volume fraction error: |0.31 - 0.30| = 0.01 (within 0.02 tolerance)"
  - "Convergence: |delta_J/J| = 8e-4 at iteration 200 (PASS)"
assumptions:
  - "Density field parsed at threshold rho >= 0.5 for load-path check"
  - "Compliance J from Swan VTK output field taken as ground truth"
what_would_falsify: >
  Independent FEA (CalculiX) on the solid region mesh gives compliance
  deviating > 15% from Swan's reported J.
provenance: "swan_topology_antagonist v1.0.0 — reviewed at [timestamp]"
confidence: 0.80
```

---

## Audit Checklist

The antagonist applies all checks below. A FATAL objection triggers an automatic FAIL.
Two or more MAJOR objections trigger CONDITIONAL_PASS (re-run required).

### C1 — Load-Path Connectivity (FATAL if violated)

```
scipy.ndimage.label(density_field >= 0.5) → n_components
PASS:  n_components == 1
FAIL:  n_components > 1  → raise FATAL LOAD_PATH_DISCONNECTED
       Resolution: increase volume fraction target by 0.05, re-run Swan
```

### C2 — Volume Fraction Accuracy (MAJOR if violated)

```
|volume_fraction_achieved - volume_fraction_target| <= 0.02
PASS:  within tolerance
MAJOR: outside tolerance → code VOLUME_DRIFT
       Resolution: switch optimizer to MMA or AugmentedLagrangian
```

### C3 — Filter Presence (MAJOR if absent)

```
filterCostType must NOT be {[]} for any cost term
PASS:  'P1' or 'PDE' confirmed
MAJOR: no filter → code CHECKERBOARD_RISK
       Resolution: activate filterCostType = {'P1'} minimum
```

### C4 — Convergence Quality (MAJOR if violated)

```
Over last 10 iterations: |delta_J / J| <= 1e-3
PASS:  criterion met
MAJOR: criterion not met → code CONVERGENCE_MARGINAL
       Resolution: increase maxiter or switch optimizer
```

### C5 — AM Constraint Completeness (MINOR if missing)

```
If am_constraints_applied = true in swan_topology_summary:
  - perimeter term must appear in cost with weight > 0
  - filterCostType for perimeter term must be 'PDE' (not 'P1')
  - filter metric must be 'Isotropy' or 'Anisotropy'
MINOR if any of the above absent → code AM_CONSTRAINT_INCOMPLETE
```

### C6 — Density Threshold Policy (MINOR if violated)

```
Density thresholds (from topology_optimization.yaml policy):
  solid:   rho >= 0.5
  lattice: 0.2 <= rho < 0.5
  void:    rho < 0.2

Violation: specialist uses non-standard thresholds without justification
MINOR → code DENSITY_THRESHOLD_NONSTANDARD
```

### C7 — Lattice Handoff Block Completeness (FATAL if absent when required)

```
If intermediate-density region (0.2 <= rho < 0.5) exists in output:
  lattice_infill_handoff block MUST be present with all required fields:
    cell_size_mm, lattice_type, beam_thickness_mm, target_volume_fraction,
    beam_thickness_gradient, nsub_sample, conformal, conformal_base_shape
FATAL if block absent → code LATTICE_HANDOFF_MISSING
MAJOR if block present but missing fields → code LATTICE_HANDOFF_INCOMPLETE
```

### C8 — Provenance Completeness (MINOR if incomplete)

```
provenance field must include:
  - Swan version or commit hash
  - Input parameter hash (SHA256)
MINOR if any absent → code PROVENANCE_INCOMPLETE
```

---

## Escalation Flags

Raise **[ANTAGONIST OVERRIDE — VAULT WRITE BLOCKED]** when verdict = FAIL.
Vault writes are unconditionally blocked until specialist re-runs and PASS is issued.

Raise **[CONDITIONAL PASS — REVIEW REQUIRED]** when two or more MAJOR objections
are present. Vault write is permitted only after human review sign-off.

---

## Known Failure Patterns Caught

Objections previously caught by this agent or analogous reviews:

- **Disconnected topology passed as connected**: specialist omitted
  `scipy.ndimage.label` check — multiple load islands passed to manufacturing.
- **Volume fraction silently drifted to 0.45 (target 0.30)**: bisection optimizer
  failed to converge; specialist did not check achieved vs target — mass budget violated.
- **No PDE filter on perimeter term**: P1 filter used for perimeter — mesh-dependent
  length scale, AM constraints meaningless.
- **Lattice handoff block absent**: intermediate density present, specialist skipped
  handoff — `lattice_infill_specialist` hard-failed downstream.
- **Anisotropy weight undocumented**: specialist used `weights = [1, 0.2]` but did not
  document the physical interpretation of the anisotropy weight in assumptions.
- **Compliance reported without units**: J reported as a raw number — load scaling
  unknown, value meaningless without N·mm or J units.

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Core audit checklist C1–C8 |
| 2 | Apprentice | 0.40–0.59 | Sensitivity challenge (volfrac +/-0.05 re-run) |
| 3 | Journeyman | 0.60–0.74 | Independent FEA cross-check via CalculiX |
| 4 | Expert | 0.75–0.89 | Multi-method comparison critique (Swan vs FreeTO) |
| 5 | Master | 0.90–1.00 | Novel failure mode identification, academic peer review |

---

## Academic Writing and Peer Review

### Academic Capability Unlocks

| Level | Capability |
|---|---|
| 3 | Write critique section: identify numerical artefacts in published topo-opt results |
| 4 | Peer review of specialist academic output — rate objections minor/major/fatal |
| 5 | Full comparative panel: Swan vs FreeTO vs ToPy on same problem |

---

## References

- Swan source (local): `swan-topology/`
- `swan_topology_specialist` SKILL: `forge-agents/swan_topology_specialist/SKILL.md`
- `topology_optimization` SKILL: `forge-agents/topology_optimization/SKILL.md`
- Load-path connectivity: scipy.ndimage.label (SciPy documentation)
- Volume constraint audit: Bendsoe and Sigmund (2003), Topology Optimization
- Checkerboard instability: Sigmund and Petersson (1998), SMO

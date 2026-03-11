# Engineering Constitution

> Four-tiered set of inviolable engineering principles.
> Every agent output is critiqued against these. Tier 1 violations halt the pipeline.
> Stored as YAML for machine-readable evaluation by the Quality Evaluator.

---

## Tier 1: Inviolable (Math Level)

**A Tier 1 violation halts the pipeline immediately. No physics or engineering argument overrides Tier 1.**

| Principle | Check |
|---|---|
| Conservation of energy | Work done = strain energy stored (within tolerance) |
| Conservation of mass | Mass in = mass out at all boundaries |
| Conservation of momentum | Reaction forces sum to zero net force |
| Stress equilibrium | ∇·σ + b = 0 satisfied at every element |
| Strain compatibility | Displacement field produces compatible strains |
| Dimensional homogeneity | All equations dimensionally consistent |

---

## Tier 2: Physics Level

**Override requires Tier 1 justification.**

| Principle | Check |
|---|---|
| Material realizable | E > 0, 0 ≤ ν ≤ 0.5, σ_yield > 0, ρ > 0 |
| Flow regime correct | Reynolds number matches turbulence model choice |
| Mesh boundary layer | y+ appropriate for wall treatment (y+≈1 for low-Re, y+>30 for wall functions) |
| Thermal bounds | No computed temperatures above material melting point |
| Pressure realizable | No negative absolute pressures (unless cavitation model active) |
| Eigenvalue positivity | Global stiffness matrix positive definite (no rigid body modes without BCs) |

---

## Tier 3: Engineering Level

**Override permitted with documented Tier 2 justification.**

| Principle | Check |
|---|---|
| Code safety factors | Safety factors meet applicable code (ASME, Eurocode, FAR) |
| Mesh convergence | <5% change in QoI between successive refinements |
| Load justification | All loads traced to requirements document |
| BC justification | All boundary conditions physically justified |
| Manufacturability | Minimum wall thickness, minimum radius per manufacturing process |
| Fatigue life | If cyclic loading present, fatigue analysis performed (not just static) |

---

## Tier 4: Best Practice

**Override permitted with documented justification.**

| Practice | Guidance |
|---|---|
| Start coarse, refine | Begin with coarse mesh, refine systematically (not all at once) |
| Grid independence | At least 3 mesh levels for grid convergence index |
| Cross-reference materials | Material properties from ≥2 independent sources |
| Analytical validation | Compare with beam theory, plate theory, or other closed-form where possible |
| Sensitivity analysis | Check sensitivity to key assumptions (E, BC type, load magnitude) |
| Document assumptions | Every non-obvious assumption explicitly stated |

---

## Machine-Readable Version

See `forge-learning/configs/engineering_constitution.yaml` for the YAML version consumed by the Quality Evaluator.

---

## Constitutional Gate Integration

The Quality Evaluator checks every agent output against all four tiers. The verification stack's Assumption Gate (V1) uses Tier 4 principles to check for hidden assumptions.

The evaluator maps tier violations onto the standard error / warning / info signals defined in
`docs/contracts/error-codes.md` (see that document for the complete, versioned catalog). Conceptually:

- Tier 1 violation → pipeline halt + escalation
- Tier 2 violation → gate failure + output rejection
- Tier 3 violation → warning + justification required
- Tier 4 miss → informational note in output (no block)

---

## Computable Checks (never debated)

These specific Tier 1-2 checks are implemented as **deterministic Python functions** and run automatically after every FEA/CFD result. They never enter the LLM debate protocol.

### FEA Automated Checks

```python
def check_reaction_equilibrium(result: CalculiXResult,
                                applied_loads: list[Load],
                                tolerance_pct: float = 1.0) -> ConstitutionGateResult:
    """Tier 1: sum of reaction forces ≈ sum of applied loads."""
    reaction_sum = sum_reaction_forces(result.reactions)
    applied_sum = sum_applied_forces(applied_loads)
    error_pct = abs(reaction_sum - applied_sum) / abs(applied_sum) * 100
    if error_pct > tolerance_pct:
        return ConstitutionGateResult(
            tier=1, pass_=False,
            error_code="ERR_CONSTITUTION_TIER1",
            detail=f"Reaction equilibrium error {error_pct:.1f}% > {tolerance_pct}%"
        )
    return ConstitutionGateResult(tier=1, pass_=True)

def check_energy_balance(result: CalculiXResult, tolerance_pct: float = 5.0):
    """Tier 1: strain energy ≈ external work done."""
    ...

def check_mesh_convergence(coarse: CalculiXResult, medium: CalculiXResult,
                            fine: CalculiXResult, qoi_field: str = "von_mises"):
    """Tier 3: Richardson extrapolation GCI < 5%."""
    ...

def check_stress_singularity(result: CalculiXResult) -> list[SingularityWarning]:
    """Tier 3: flag stress concentrations that may be singularities (re-entrant corners)."""
    ...
```

### CFD Automated Checks

```python
def check_residual_convergence(log: OpenFOAMLog, threshold: float = 1e-4):
    """Tier 2: all residuals converged below threshold."""
    ...

def check_mass_conservation(log: OpenFOAMLog, tolerance_pct: float = 0.1):
    """Tier 1: mass flux balance at all boundaries."""
    ...

def check_y_plus(result: OpenFOAMResult, wall_treatment: str):
    """Tier 2: y+ appropriate for turbulence wall treatment."""
    ...
```

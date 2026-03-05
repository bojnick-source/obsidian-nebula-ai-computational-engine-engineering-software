# Aladdin-3B Pipeline Map

> Current project focus: smart fuselage / structural path first (motor mount bracket).

---

## MVP Pipeline (v0.1)

```
Input: Motor mount bracket structural analysis request
  │
  ▼
Task Intake → Trace ID → Blackboard Init
  │
  ▼
Skill Router → engineering_full → structural_analysis workflow
  │
  ▼
System Decomposition
  ├── Constraints: 6061-T6 aluminum, max_stress < 0.6 × σ_yield
  ├── Load cases: max_thrust_static
  ├── Assumptions: linear elastic, quasi-static
  └── Gaps: (none at MVP test)
  │
  ▼
Memory Pre-Flight (Librarian)
  ├── Retrieve: domain=mechanical_engineering, component=motor_mount_bracket
  └── Context package assembled
  │
  ▼
ME Specialist (prompt v1.0.0)
  ├── Structural analysis: loads, stresses, safety factor
  ├── Material: 6061-T6 (provenance: ASM Handbook)
  └── Output: agent_output_contract v1
  │
  ▼
GMSH Wrapper (MCP)
  ├── Input: geometry spec (parametric bracket definition)
  ├── Output: mesh file (.msh)
  └── Validation: non-zero elements, no degenerates
  │
  ▼
CalculiX Wrapper (MCP)
  ├── Input: mesh + boundary conditions + load
  ├── Output: von Mises stress field, displacements
  └── Parse: max von Mises, displacement magnitude
  │
  ▼
Verification Stack
  ├── Contract Gate: PASS
  ├── Unit Gate: PASS (MPa, N, mm)
  ├── Dimensional Gate: PASS
  └── Provenance Gate: PASS
  │
  ▼
Vault Persistence (Librarian)
  ├── Note type: finding
  ├── Domain: mechanical_engineering
  ├── Component: motor_mount_bracket
  └── Amnesia check: PASS
  │
  ▼
Output Report
  ├── Result summary
  ├── Safety factor
  ├── Unresolved gaps
  ├── what_would_falsify
  └── Artifact refs (vault note ID)
```

---

## V1 Pipeline Extensions

- OpenVSP: outer mold line definition
- JSBSim: flight dynamics envelope
- FreeTO: topology optimization of bracket
- Empirical crosscheck: compare FEA results to known benchmarks
- ME + Materials antagonist debate: challenge material assumptions
- Contradiction gate: check against existing vault findings

---

## Component Targets (Aladdin-3B)

| Priority | Component | Analysis Type | Status |
|---|---|---|---|
| MVP | Motor mount bracket | Linear static FEA | In spec |
| V1 | Wing spar (simplified) | Static + fatigue | Planned |
| V1 | Landing gear attachment | Static + fatigue | Planned |
| V1 | Full fuselage skin | Buckling | Planned |
| V1+ | Full OML | Aerodynamic (CFD) | Planned |

---

## Constraints

See `docs/projects/aladdin-3b/constraints.md`.

## Assumptions

See `docs/projects/aladdin-3b/assumptions.md`.

## Acceptance Scenarios

See `docs/projects/aladdin-3b/acceptance-scenarios.md`.

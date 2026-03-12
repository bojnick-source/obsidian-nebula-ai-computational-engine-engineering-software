# ME Specialist — SKILL Definition

**Agent ID:** `me_specialist`
**Domain:** Mechanical Engineering — Structural Analysis
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The ME Specialist performs linear static FEA on mechanical components using
CalculiX (via MCP wrapper), then synthesizes results into an engineering finding
with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Linear static FEA (GMSH + CalculiX) | Active (MVP) | Core capability |
| Material selection (4130, Al7075, Ti-6Al-4V) | Active | MMPDS-12 database |
| Boundary condition specification | Active | Fixed, force, pressure, symmetry |
| Safety factor calculation (yield-based) | Active | SF = σ_y / σ_max |
| Mesh convergence assessment | Active | Manual + automated GCI check |
| Non-linear FEA | Planned (V1) | NLGEOM flag when ε > 5% |
| Fatigue analysis (S-N) | Planned (V1) | Basquin equation |
| Thermal stress | Planned (V1) | ΔT loading |
| Topology optimization (FreeTO) | Planned (V1) | Post-analysis optimization |

### Tools Allowed

```yaml
tools_allowed:
  - gmsh       # Mesh generation
  - calculix   # Linear static FEA
```

### Mandatory Output Fields

Every ME Specialist output MUST include:
1. `findings` — list of specific numerical results (MPa, mm, SF values)
2. `assumptions` — NEVER null; minimum: material linearity, small deformations
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — CalculiX version + input file hash
5. `confidence` — float 0.0–1.0

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Maximum von Mises stress: XX.X MPa at [location]"
  - "Maximum displacement: X.XX mm at [location]"
  - "Safety factor (yield): X.X (yield strength: XXX MPa)"
assumptions:
  - "Material behavior is linear elastic (ε < 5% — verified)"
  - "Boundary conditions approximate [physical condition]"
  - "Geometric nonlinearity neglected (small displacement assumption)"
what_would_falsify: >
  Plastic deformation observed in physical test at loads below XX N;
  or mesh convergence study shows GCI > 5% at stated element count.
provenance: "CalculiX 2.21 — input file SHA256: [hash]"
confidence: 0.85
```

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Basic linear static |
| 2 | Apprentice | 0.40–0.59 | Mesh convergence automation |
| 3 | Journeyman | 0.60–0.74 | Non-linear FEA |
| 4 | Expert | 0.75–0.89 | Fatigue, thermal |
| 5 | Master | 0.90–1.00 | Topology optimization |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Rigid body mode**: Missing sufficient boundary conditions → singular stiffness matrix
- **Unit mismatch**: Force in N but material in MPa requires consistent unit system
- **Singularity at sharp re-entrant corners**: Add fillet radius ≥ element size

---

## Tool Parameter Preferences

See forge-learning/tool_memory/calculix/parameter_prefs.yaml for latest.

Quick reference:
- Default element: C3D10 (10-node tet)
- Solver: SPOOLES
- Fillet mesh refinement: 0.25× nominal size

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
  content_latex: "..."
  equations_numbered: true
  notation_consistency: true

peer_review_verdict:
  target_agent_id: "..."
  target_run_id: "..."
  decision: "major_revision"
  objections: []
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

---
## Escalation Flags

- Yield/safety margin < 1.0: **HALT** — escalate to forge_arbiter
- Results diverge > 15% from analytical baseline: escalate to senior specialist
- Missing provenance on any tool call: reject and re-run with version pinning

---
## References

- MMPDS-12 for material allowables
- ASME V&V 10 for FEA verification procedures
- NAFEMS Best Practice Guidelines
- forge-tools/mcp-wrappers/calculix/ for wrapper spec

# FORGE Roadmap

> Tiered roadmap: MVP → V1 → R&D. Gates must be passed sequentially.

---

## MVP (v0.1) — Structural Analysis Path

**Goal:** End-to-end single-discipline structural analysis run for one Aladdin-3B component (motor mount bracket), fully traced and persisted.

**Exit Gate:** v0.1 acceptance test passes. See `docs/planning/mvp/v0.1-acceptance-test.md`.

### MVP Scope

| Component | Description |
|---|---|
| Blackboard | Typed entry, schema v1, concurrent-safe writes |
| Config loader | YAML config with schema versioning |
| Model router | Single-provider (no failover required at MVP) |
| ME Specialist | Prompt v1.0.0, structural analysis only |
| GMSH wrapper | MCP envelope, mesh generation, basic validation |
| CalculiX wrapper | MCP envelope, linear static FEA, result parsing |
| Structural Verifier | Contract gate + unit gate + dimensional gate |
| Provenance Gate | Basic source attribution check |
| Vault write | Frontmatter schema v1, finding note type |
| Retrieval sanity | Amnesia check after write |
| JSONL logger | Trace ID propagation, error codes |
| Trace IDs | Generation, propagation, attachment to all artifacts |

### MVP Exclusions (explicit cut line)

- Antagonist/debate phase
- Contradiction gate (vault lookup)
- Confidence calibration
- Provider failover/circuit breaker
- ILC links
- CFD, topology optimization, any non-structural solver
- External CAD import
- Cost tracking events
- HashiCorp Vault secrets (use env vars at MVP)

---

## V1 — Multi-Discipline Pipeline

**Goal:** Full multi-discipline analysis with antagonist debate, contradiction handling, provider failover, and expanded toolchain.

**Entry Gate:** v0.1 acceptance test passed and frozen.

### V1 Additions

| Area | Additions |
|---|---|
| Agents | Antagonist pairs, A2A debate lifecycle, arbitration |
| Memory | ILC link detection, synthesis, decay detection, thinking catalog |
| Tools | FreeTO (topology opt), OpenFOAM/SU2 (CFD), XFOIL, OCCT, PicoGK, OpenVSP, JSBSim |
| Verification | Contradiction gate, assumption gate, adversarial falsification, confidence calibration |
| Ops | Provider failover, circuit breaker, cost tracking, HashiCorp Vault secrets |
| Geometry | CATIA/Solid Edge import, validation gates, visual vs. engineering classification |
| Projects | Vanguard pipeline, Phoenix initial scaffold |
| Intelligence | Video intelligence layer, empirical crosscheck |

---

## R&D — Advanced Capabilities

**Goal:** Experimental capabilities for evaluation. Not on production critical path.

| Area | Capability |
|---|---|
| RTSA | Runtime topological self-assembly (state graph, transition verifier) |
| NVIDIA Physics | PhysX, Warp, Newton, PhysicsNeMo integration |
| Simulation | Gazebo Harmonic, Isaac Sim, Pegasus, OmniDrones |
| Topology Opt | Swan (license-conditional), OpenLSTO |
| FEA | FEniCSx, preCICE multi-physics coupling |
| Emergent Agents | ILC-triggered agent synthesis (human approval gate required) |
| Digital Twins | O3DE integration for Project Vanguard |

---

## Milestone Gates

| Milestone | Gate Criteria | Artifacts |
|---|---|---|
| v0.1 | Acceptance test passes end-to-end | `docs/planning/mvp/v0.1-acceptance-test.md` |
| v0.1a | Degraded mode path tested | `docs/planning/mvp/v0.1a-fallback-spec.md` |
| v1.0 | All V1 additions integrated, full red-team pass | `forge-tests/reports/` |
| R&D | Per-capability evaluation gates | TBD per capability |

See `docs/planning/roadmap/milestone-gates.md` for detailed gate criteria.

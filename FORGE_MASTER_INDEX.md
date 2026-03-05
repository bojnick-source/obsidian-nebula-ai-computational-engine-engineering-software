# FORGE Master Index

> **One-page planning index. Keep this current. If it contradicts another doc, this wins.**

---

## Current State

| Field | Value |
|---|---|
| Catalog Version | v8+ (execution addendum integrated) |
| Active Milestone | v0.1 MVP — structural analysis path (Aladdin-3B motor mount bracket) |
| Planning Phase | Lane A — baseline freeze candidate |
| Build Phase | Not started |

---

## Critical Path (v0.1 MVP)

```
Task Intake → Blackboard Init → ME Specialist → GMSH (mesh) → CalculiX (FEA)
→ Verification Stack → Vault Persistence → Output Report
```

**Minimum viable chain:** Blackboard + ME specialist + GMSH wrapper + CalculiX wrapper + structural verifier + vault write.

---

## Frozen Interfaces

| Interface | Status | Doc |
|---|---|---|
| Blackboard Schema v1 | FROZEN | `docs/contracts/blackboard-schema.md` |
| Agent Output Contract v1 | FROZEN | `docs/contracts/agent-output-contract.md` |
| MCP Wrapper Envelope v1 | FROZEN | `docs/contracts/mcp-wrapper-envelope.md` |
| Vault Frontmatter Schema v1 | FROZEN | `docs/contracts/vault-frontmatter-schema.md` |
| Trace ID Standard v1 | FROZEN | `docs/contracts/trace-id-standard.md` |
| Error Codes v1 | FROZEN | `docs/contracts/error-codes.md` |

---

## Deferred Subsystems (not before v0.1)

- Antagonist/debate phase (A2A)
- ILC link synthesis
- Emergent agent synthesis
- RTSA (runtime topological self-assembly)
- NVIDIA physics stack
- CFD wrappers (OpenFOAM, SU2)
- Topology optimization (FreeTO, Swan)
- External CAD imports (CATIA, Solid Edge)
- Video intelligence
- Empirical crosscheck layer

---

## Top 3 Risks

| # | Risk | Trigger | Mitigation |
|---|---|---|---|
| 1 | Solver wrapper unreliability (CalculiX/GMSH subprocess) | >2 consecutive failures in CI | Degraded mode: stub solver + flag for manual review |
| 2 | Vault amnesia (memory not persisting/retrieving correctly) | Retrieval sanity test fails | Halt pipeline; vault is a hard dependency |
| 3 | Planning scope creep before build starts | New subsystem added without P0 justification | Planning cut line enforced; addendum intake rules apply |

---

## Priority Tags

- **P0** — Must exist and be frozen before first build starts
- **P1** — Can be finalized during build (not required to start)
- **P2** — Future planning (V1 / R&D phase)

### P0 Documents (must freeze first)

- [ ] This index
- [ ] `docs/planning/catalog/forge-catalog-current.md`
- [ ] `docs/planning/mvp/v0.1-spec.md`
- [ ] `docs/planning/mvp/v0.1-acceptance-test.md`
- [ ] `docs/planning/mvp/mvp-cut-line.md`
- [ ] All `docs/contracts/` files
- [ ] `docs/architecture/system-overview.md`
- [ ] `docs/architecture/core-loop.md`
- [ ] `docs/architecture/degraded-modes.md`
- [ ] `docs/planning/risk/risk-register.md`
- [ ] `docs/planning/roadmap/tiered-roadmap.md`
- [ ] Phase 1.x fixtures (blackboard, memory, thinking)
- [ ] Red-team verifier fixture pack
- [ ] Decision log (frozen choices only)

---

## Canonical Toolchain (v0.1 MVP)

| Tool | Role | Status |
|---|---|---|
| GMSH | Mesh generation | MVP |
| CalculiX | FEA solver | MVP |
| FreeTO | Topology optimization | V1 |
| OpenFOAM | CFD | V1 |
| SU2 | CFD | V1 |
| XFOIL | 2D aero | V1 |
| OCCT | Geometry kernel | V1 |
| PicoGK | Volumetric geometry | V1 |
| OpenVSP | Aircraft geometry | V1 |
| JSBSim | Flight dynamics | V1 |

---

## Active Build Lane

**Lane A** (Planning Canon) — in progress
**Lane B** (Core Runtime) — next

---

*Last updated: 2026-03-05*

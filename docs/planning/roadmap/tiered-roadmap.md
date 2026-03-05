# Tiered Roadmap

> See ROADMAP.md at repo root for summary. This is the detailed version.

---

## Tier 0: Planning Baseline (Current)

**Status:** In progress
**Goal:** Freeze planning canon before first line of build code.

P0 documents — must all be complete:
- [x] FORGE Master Index
- [x] Catalog v8+ (integrated)
- [x] v0.1 MVP Spec + Acceptance Test
- [x] MVP Cut Line
- [x] Tiered Roadmap
- [x] Risk Register
- [x] Decision Log
- [x] All contract docs (blackboard, agent output, MCP envelope, vault frontmatter, trace ID, error codes)
- [x] Architecture docs (overview, core loop, agent topology, memory model, verifier, degraded modes, MCP/A2A, observability)
- [ ] Phase 1.x fixtures (placeholder structure created; fixture content pending)
- [ ] Red-team verifier fixture pack (placeholder structure created; cases pending)

---

## Tier 1: MVP (v0.1)

**Entry gate:** Planning baseline frozen (all P0 docs complete)
**Exit gate:** v0.1 acceptance test (all 10 AC pass)

### Build sequence (Lane B → C → E → F first)

**Week 1–2: Core Runtime Spine (Lane B)**
- Blackboard implementation (typed entries, schema v1, concurrency guard)
- Config loader (YAML, schema versioning)
- JSONL logger (trace ID, error codes)
- Model router (single provider)
- Basic orchestrator (phase sequencing, loop guard)

**Week 3–4: Memory Core (Lane C)**
- Vault manager (write, read, frontmatter validation)
- Intake logic
- Retrieval routing (domain + component filter)
- Amnesia check

**Week 5–6: Tool Wrappers (Lane E)**
- GMSH MCP wrapper
- CalculiX MCP wrapper
- Subprocess sandbox
- Degraded mode stubs

**Week 7–8: Verification (Lane F)**
- Contract Gate
- Unit Gate
- Dimensional Gate
- Provenance Gate

**Week 9: Integration + Aladdin-3B (Lane I)**
- ME Specialist prompt v1.0.0
- Librarian (intake + retrieval)
- End-to-end happy path
- Acceptance test run

**Week 10: v0.1a Fallback + Polish**
- Degraded mode path
- Error handling hardening
- Log completeness check

---

## Tier 2: V1 (v1.0)

**Entry gate:** v0.1 acceptance test passed and frozen.

### Build sequence
- Antagonist system + A2A debate (Lane D)
- Provider failover + circuit breaker (Lane H)
- Contradiction gate + assumption gate + adversarial verifier + confidence calibration (Lane F)
- FreeTO + OpenFOAM + SU2 + XFOIL wrappers (Lane E)
- OCCT + PicoGK + OpenVSP + JSBSim wrappers (Lane E)
- Memory: ILC link detection, synthesis, decay detection, thinking catalog (Lane C)
- HashiCorp Vault secrets + cost tracking (Lane H)
- Video intelligence + empirical crosscheck (Lane E)
- External CAD import (CATIA, Solid Edge) + geometry validation gate (Lane J-bridge)
- Vanguard pipeline (Lane I)
- Phoenix initial scaffold (Lane I)

---

## Tier 3: R&D

**Entry gate:** V1 complete and stable.

Capabilities evaluated independently:
- RTSA (runtime topological self-assembly)
- NVIDIA physics stack (PhysX, Warp, Newton, PhysicsNeMo)
- Simulation environments (Gazebo, Isaac Sim, Pegasus, OmniDrones)
- Swan topology optimization (license-conditional)
- O3DE digital twin (Project Vanguard)
- Emergent agent synthesis (ILC-triggered, human approval gate)
- FEniCSx / preCICE for PDE-heavy workloads

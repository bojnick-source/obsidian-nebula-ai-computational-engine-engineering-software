# FORGE Decision Log (Frozen Decisions)

> ADR-style frozen decisions. These are closed. Do not reopen without a new ADR.

---

## ADR-001: Monorepo for Planning Phase

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Repo-of-repos vs. monorepo for initial planning scaffold.
**Decision:** Start as a monorepo. Top-level directories mirror future repo-of-repos structure. Split when operational complexity justifies it.
**Consequences:** Simpler CI, single clone, easier cross-component refactoring in early phases.

---

## ADR-002: C++ for Core Runtime Orchestration Spine

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Python vs. C++ vs. Go for the orchestration runtime.
**Decision:** C++ for the core runtime (blackboard, routing, orchestration, A2A/MCP dispatch). Python allowed for wrappers, test harness, and tooling scripts.
**Consequences:** Higher performance ceiling, deterministic memory, but slower initial development vs. Python. Justified by engineering reliability requirements.

---

## ADR-003: Obsidian as Neural Memory Backend

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Vector DB vs. graph DB vs. file-based knowledge system for memory.
**Decision:** Obsidian vault with structured YAML frontmatter as the knowledge persistence layer. Git-backed for provenance. Custom routing/synthesis logic on top.
**Consequences:** Human-readable, git-trackable, provenance-native. Trade-off: no native vector search at MVP (keyword + frontmatter routing only). Vector augmentation is a V1 consideration.

---

## ADR-004: MCP for Tool Invocation

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Direct subprocess vs. REST vs. MCP for solver invocation.
**Decision:** MCP (Model Context Protocol) wrappers for all external tools. Each tool gets a wrapper spec, input schema, output schema, and error contract.
**Consequences:** Uniform invocation interface, consistent error handling, testable in isolation. Subprocess sandboxing policy applies to all wrappers.

---

## ADR-005: A2A for Agent-to-Agent Communication

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Direct function calls vs. message bus vs. A2A protocol for agent communication.
**Decision:** A2A (Agent-to-Agent) protocol for inter-agent communication. gRPC transport for production; local shim for testing.
**Consequences:** Decoupled agents, testable debate lifecycle, transport-agnostic at the agent level. Deferred to V1; MVP uses single-specialist path.

---

## ADR-006: HashiCorp Vault for Secrets Management

**Status:** Accepted
**Date:** 2026-03-05
**Context:** .env files vs. cloud secrets manager vs. HashiCorp Vault.
**Decision:** HashiCorp Vault with AppRole authentication for all secret management. Pre-commit git secret scanning enforced.
**Consequences:** Consistent secrets model, rotation support, audit trail. MVP uses env vars as a temporary shortcut only; HCV required before V1.

---

## ADR-007: CalculiX + GMSH as MVP FEA Stack

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Multiple open-source FEA stacks evaluated (FEniCSx, Elmer, CalculiX).
**Decision:** CalculiX for FEA solver + GMSH for mesh generation as the MVP structural analysis stack. Both are open-source, well-documented, and have Python APIs for MCP wrapping.
**Consequences:** Strong community support for aerospace/structural use cases. FEniCSx considered for V1 as a complementary option for PDE-heavy workloads.

---

## ADR-008: Verification is Non-Negotiable

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Should verification be optional/configurable at MVP?
**Decision:** No. The full verification stack (contract, unit, dimensional, provenance) must run on every output. Adversarial and contradiction gates are deferred to V1 but their architecture is frozen now.
**Consequences:** Higher bar for MVP completion but prevents unverified results ever entering the vault.

---

## ADR-009: Planning Cut Line

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Risk of indefinite planning without build starting.
**Decision:** No new subsystems added to planning without P0 justification. Addendum intake process required. Normalization scheduled after each planning phase ends.
**Consequences:** Forces prioritization. P2 ideas go to the catalog backlog, not the active planning scope.

---

## ADR-010: FreeTO over Swan for MVP Topology Optimization

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Swan (academic license uncertainty) vs. FreeTO (open-source) for topology optimization.
**Decision:** FreeTO as primary topology optimization tool (V1 scope). Swan as R&D conditional on license resolution. beso as V1 secondary fallback.
**Consequences:** Unblocks topology optimization path. Swan tracked in risk register (R-10).

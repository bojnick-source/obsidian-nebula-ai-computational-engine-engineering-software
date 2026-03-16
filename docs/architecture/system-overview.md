# FORGE System Overview

> **Status:** P0 — must be frozen before build starts.

---

## What FORGE Is

FORGE is an engineering-grade multi-agent AI orchestration system. It ingests engineering design problems, orchestrates specialist AI agents against versioned tools (FEA, CFD, topology optimization), enforces a verification trust boundary, and persists all reasoning in a provenance-tracked neural memory (Obsidian vault).

FORGE is **not** a large language model, a CAD tool, or a data warehouse. It is a reasoning orchestration system that wraps and verifies the outputs of both AI agents and deterministic solvers.

---

## Top-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FORGE SYSTEM                                │
│                                                                     │
│  ┌──────────────┐    ┌──────────────────────────────────────────┐  │
│  │  Task Intake │───▶│           ORCHESTRATOR                   │  │
│  │  (trace IDs) │    │  (task graph, dependency DAG, dispatch)  │  │
│  └──────────────┘    └──────────┬───────────────────────────────┘  │
│                                 │                                   │
│       ┌─────────────────────────┼──────────────────┐               │
│       ▼                         ▼                  ▼               │
│  ┌─────────┐          ┌──────────────┐     ┌───────────────┐       │
│  │BLACKBOARD│         │  AGENT SYSTEM │     │  TOOL LAYER   │       │
│  │(shared  │◀────────▶│  (specialists │     │  (MCP wrappers│       │
│  │ state)  │         │   antagonists │     │   CalculiX    │       │
│  └─────────┘         │   verifiers  │     │   GMSH, etc.) │       │
│                      │   librarian) │     └───────┬───────┘       │
│                      └──────┬───────┘             │               │
│                             │                     │               │
│                      ┌──────▼─────────────────────▼───────┐       │
│                      │       VERIFICATION STACK            │       │
│                      │  contract→unit→dim→provenance→      │       │
│                      │  contradiction→assumption→adversarial│      │
│                      └──────────────────┬──────────────────┘       │
│                                         │                          │
│                      ┌──────────────────▼──────────────────┐       │
│                      │         MEMORY SYSTEM               │       │
│                      │  (Obsidian vault + routing +        │       │
│                      │   synthesis + contradiction)        │       │
│                      └─────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Invariants

1. **Every result is traced.** All outputs carry a trace ID from intake to vault.
2. **Verification is mandatory.** No unverified data enters the vault.
3. **Contracts are frozen.** Interface changes require a version bump and ADR.
4. **Memory is persistent.** The vault is the system of record. In-memory state is ephemeral.
5. **Degraded modes are planned.** Every critical path has a documented fallback.

---

## Component References

| Component | Spec Location |
|---|---|
| Core Runtime | `forge-core/README.md` |
| Agent System | `forge-agents/README.md` |
| Memory System | `forge-memory/README.md` |
| Tool Layer | `forge-tools/README.md` |
| Verification | `forge-verification/README.md` |
| Data Contracts | `docs/contracts/` |
| Ops | `forge-ops/README.md` |

---

## Related Docs

- [Polyglot Architecture Doctrine](polyglot-doctrine.md)
- [Core Loop](core-loop.md)
- [Agent Topology](agent-topology.md)
- [Memory Neural Model](memory-neural-model.md)
- [Verifier Architecture](verifier-architecture.md)
- [MCP/A2A Boundaries](mcp-a2a-boundaries.md)
- [Degraded Modes](degraded-modes.md)
- [Observability Standard](observability-standard.md)

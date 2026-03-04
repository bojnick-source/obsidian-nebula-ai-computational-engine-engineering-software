# FORGE Decision Log (ADR Format)

Architectural Decision Records for the FORGE project. Each ADR captures the
context, decision, and consequences of a significant architectural choice.

> **Protocol**: New ADR entries may be added during implementation when
> architectural decisions are made. This is the one exception to the
> Planning Freeze (see ADR-007).

---

### ADR-001: Language Selection — Python for MVP

**Status**: Accepted
**Date**: 2026-03-02

**Context**:
DARK_leaf v2 assumed C++ was necessary for performance. This led to weeks of
toolchain setup (CMake, vcpkg, Conan) with zero agent implementation progress.
The actual performance bottleneck is LLM API latency (100–2000ms per call),
not local compute. Python has superior ecosystem support for LLM orchestration
(LangChain, LiteLLM, httpx) and faster development velocity.

**Decision**:
Python is the sole implementation language for the MVP. All agents, the
orchestrator, model router, blackboard, and CLI are implemented in Python.
C++ is deferred to V1-17 and only pursued if Python latency exceeds defined
targets (orchestration loop < 500ms, blackboard R/W < 10ms, vault I/O < 50ms).

**Consequences**:
- Faster development: Python's dynamic typing and REPL allow rapid iteration.
- Library access: Direct use of httpx, pydantic, pytest, PyYAML.
- Risk: If latency targets are not met, a C++ port adds 4–8 weeks to V1.
- Mitigated by: Latency validation during M5 performance testing.

---

### ADR-002: Agent Scope — 7 Agents for MVP

**Status**: Accepted
**Date**: 2026-03-02

**Context**:
The DARK_leaf v2 design specified 68 agents across 12 domains. None were
implemented end-to-end. The evaluation rubric penalized the project for
"untested agent pipeline" (−8 points). Analysis showed that 7 agents cover
the core pipeline (orchestration, analysis, verification, persistence, testing)
and are sufficient to demonstrate the architecture.

**Decision**:
The MVP includes exactly 7 agents: Orchestrator (ORCH-01), ME Specialist (E-01),
Materials Specialist (E-05), Structural Verifier (V-STRUCT), Adversarial
Verifier (V-ADV), Librarian (LIB-01), and Pipeline Tester (TEST-01). The
remaining 61 agents are archived in `docs/planning/catalog/` for V1 evaluation.

**Consequences**:
- Focus: Each agent can be properly implemented, tested, and validated.
- Risk: Some engineering domains (thermal, fluids, electrical) are not covered.
- Mitigated by: The 7 agents cover the structural/mechanical domain completely,
  which is sufficient for the MVP demonstration.
- V1 promotion criteria: An archived agent is promoted only after the MVP
  pipeline is stable and the agent's domain has validated test fixtures.

---

### ADR-003: Supermemory Optional — Degraded Mode Fallback

**Status**: Accepted
**Date**: 2026-03-02

**Context**:
The original architecture required Supermemory (external API) for knowledge
persistence. Integration was attempted during M2 and proved unreliable —
the API was intermittently unavailable and added latency to every vault
operation. The Obsidian vault provides sufficient persistence for MVP scope.

**Decision**:
Supermemory is optional. The MVP ships in "degraded" memory mode using only
the local Obsidian vault. The Librarian agent handles all read/write operations
against the file system. Supermemory integration code remains but is disabled
in `forge.yaml` (`memory.supermemory.enabled: false`).

**Consequences**:
- Reliability: No external dependency for core memory operations.
- Simplicity: File-based vault is easier to debug and version-control.
- Risk: Degraded mode lacks semantic search (Supermemory's main value-add).
- Mitigated by: The Librarian uses keyword matching and frontmatter tags for
  context retrieval, which is sufficient for MVP scope.

---

### ADR-004: C++ Port Deferred to V1-17

**Status**: Accepted
**Date**: 2026-03-02

**Context**:
DARK_leaf v2 spent significant time on C++ toolchain without validating
whether C++ performance was necessary. The FORGE architecture is I/O-bound
(LLM API calls dominate latency), not compute-bound.

**Decision**:
C++ port is deferred to V1, milestone 17. It will only be pursued if Python
latency exceeds these targets during M5 testing:
- Orchestration loop: < 500ms excluding API calls
- Blackboard read/write: < 10ms per operation
- Vault I/O: < 50ms per note read/write

**Consequences**:
- No C++ toolchain overhead in MVP development.
- Python latency is monitored throughout development.
- If targets are met, C++ is deprioritized indefinitely.
- If targets are missed, V1 adds 4–8 weeks for the port.

---

### ADR-005: Swan License Deferred — No Topology Optimization in MVP

**Status**: Accepted
**Date**: 2026-03-02

**Context**:
FreeTO (topology optimization tool) requires a Swan license. License
procurement was blocked on legal review, and topology optimization is not
required for the core structural analysis pipeline.

**Decision**:
FreeTO and topology optimization are deferred to V1. The MVP toolchain includes
only CalculiX (FEA) and GMSH (meshing), both of which are open-source.

**Consequences**:
- No license dependency or legal blocker in the MVP.
- Topology optimization use cases cannot be demonstrated.
- Mitigated by: The MVP focuses on stress analysis, deflection, and fatigue —
  domains that do not require topology optimization.

---

### ADR-006: Three-Provider MVP — Doubao Deferred

**Status**: Accepted
**Date**: 2026-03-02

**Context**:
Four providers were initially considered: Anthropic, OpenAI, DeepSeek, and
Doubao (ByteDance). Doubao's API documentation was incomplete, and its
availability outside China was uncertain. Managing four providers adds
complexity to the model router and testing matrix.

**Decision**:
The MVP uses three providers: Anthropic (primary), OpenAI (secondary), and
DeepSeek (pending validation). Doubao is deferred to V1. DeepSeek inclusion
is conditional on passing the Week 2 validation experiment.

**Consequences**:
- Simpler routing logic and fewer API integrations to maintain.
- Risk: If both Anthropic and OpenAI have outages, only unvalidated DeepSeek
  remains as fallback.
- Mitigated by: This scenario is extremely unlikely; both providers have
  >99.9% historical uptime.

---

### ADR-007: Planning Freeze — No New Planning Documents

**Status**: Accepted
**Date**: 2026-03-02

**Context**:
DARK_leaf v2 lost an estimated 3 points for "planning displacement" — sessions
that produced planning documents instead of code. Analysis showed a pattern:
each new planning document created more questions than it answered, leading
to recursive planning loops. The evaluation rubric awards zero points for
planning artifacts.

**Decision**:
After the master index (FORGE_EXECUTION_PLAN.md) is committed, no new
planning documents may be created. The three canonical documents are:
1. `FORGE_CATALOG.md` — Architecture and agent roster
2. `FORGE_EXECUTION_PLAN.md` — Timeline and process
3. `DECISIONS.md` — Architectural decision records

Edits to existing documents are limited to factual corrections. New ADR
entries in `DECISIONS.md` are the sole exception. Every coding session must
produce code, tests, or vault content.

**Consequences**:
- Forces implementation focus: no escape into planning.
- Risk: Important architectural questions may go undocumented.
- Mitigated by: ADR entries capture decisions as they arise during coding.
- Risk: Team members may create informal notes outside the repo.
- Mitigated by: The pre/post session checklists enforce the protocol.

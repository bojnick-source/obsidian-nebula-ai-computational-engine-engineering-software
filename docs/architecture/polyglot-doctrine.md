# Polyglot Architecture Doctrine

> **Status:** Frozen — architectural decision, not subject to revision without ADR.
>
> **Rule:** Right tool for the right job. Choices justified by purpose, not preference.
> AI agents help plan language allocation.

---

## Language Allocation Table

| Language / Stack | Purpose | Justification |
|---|---|---|
| **C++** | Core runtime, orchestration, blackboard, model router, agent lifecycle, A2A/gRPC, main loop | Deterministic performance, memory control, latency targets (<100 ms router, <50 ms blackboard) |
| **Python** | MCP server wrappers, tool integration, Obsidian vault interface, maintenance automation, glue, fast iteration | Ecosystem (foamlib, PyCCX, FEniCSx API, FastMCP), rapid prototyping, acceptable latency for tool dispatch |
| **MATLAB / Octave** | FreeTO, Swan, topology optimization, established math/engineering toolboxes | Existing validated code, MATLAB Engine API bridges to C++/Python, Octave fallback for unlicensed environments |
| **GPU stacks (CUDA/Python/C++)** | PhysX 5.6, Warp differentiable physics, Newton robotics, Isaac Sim, PhysicsNeMo | Physics simulation at scale requires GPU. Warp = Python→CUDA JIT. PhysX = native C++/CUDA. |
| **YAML / JSON** | Configuration, blackboard schema, forge.yaml, agent contracts, test fixtures | Human-readable, version-controllable, parseable by any language in the stack |

---

## Component ↔ Language Mapping

| Component | Language | Location |
|---|---|---|
| Core runtime loop | C++ | `forge-core/` |
| Blackboard | C++ | `forge-core/include/forge/blackboard/` |
| Model router | C++ | `forge-core/include/forge/routing/` |
| A2A transport / gRPC | C++ | `forge-core/include/forge/a2a/`, `forge-core/proto/` |
| Orchestrator | C++ | `forge-core/include/forge/orchestration/` |
| Verification stack | C++ | `forge-core/include/forge/verification/` |
| Event bus | C++ | `forge-core/include/forge/events/` |
| MCP wrappers (tools) | Python | `forge-tools/mcp-wrappers/` |
| Obsidian vault interface | Python | `forge_agent/memory/` |
| Agent loop / specialists | Python | `forge_agent/` |
| Maintenance / CI scripts | Python | `tools/` |
| FreeTO / Swan wrappers | MATLAB / Octave | `forge-tools/matlab-wrappers/` *(planned)* |
| PhysX / Warp / Isaac | GPU (CUDA / Python) | `forge-gpu/` *(planned)* |
| All config / schemas | YAML / JSON | `forge-core/configs/`, `forge-memory/schemas/` |

---

## Anti-Patterns (explicitly banned)

| Anti-pattern | Why banned |
|---|---|
| Using Python for the core runtime loop or blackboard | Python's GIL and unpredictable GC prevent sub-50 ms latency guarantees |
| Using C++ for MCP tool wrappers | Massive ecosystem cost; tools already have Python bindings (foamlib, PyCCX) |
| Using MATLAB for anything outside topology optimization / established validated toolboxes | License dependency, not embeddable in real-time path |
| Using GPU stacks for anything that doesn't require massively parallel physics | CUDA adds build complexity; only justified by simulation-at-scale requirement |
| Adding a language without an entry in this table | Every language must have a defensible purpose. No preference-driven additions. |

---

## Latency Contracts by Language

| Path | Language | Target |
|---|---|---|
| Blackboard read / write | C++ | < 50 ms |
| Model router decision | C++ | < 100 ms |
| MCP tool dispatch | Python | < 500 ms |
| Vault read / write | Python | < 1 s (async queued) |
| FEA solve dispatch | MATLAB / Python | < 60 s (solver-bound) |
| GPU physics step | CUDA | < 10 ms / step |

---

## Decision Authority

- **Changing a language assignment** requires an ADR filed in `docs/governance/decisions.md`.
- **Adding a new language** requires an ADR **and** explicit justification that no language in the
  current table can serve the purpose.
- **AI agents** (FORGE specialists, Copilot) must flag any code written in a language that
  violates this table before committing.

---

## Relationship to Toolchain

GPU and MATLAB tool stacks listed as "Evaluating" in
[`docs/toolchain/canonical-toolchain-reference.md`](../toolchain/canonical-toolchain-reference.md)
do not enter production until their language allocation is confirmed here and a wrapper
architecture is approved.

---

## Related Docs

- [System Overview](system-overview.md)
- [Core Loop](core-loop.md)
- [MCP/A2A Boundaries](mcp-a2a-boundaries.md)
- [Canonical Toolchain Reference](../toolchain/canonical-toolchain-reference.md)
- [NVIDIA Physics Stack R&D](../research/nvidia-physics-stack-rd-lane.md)
- [Swan License Paths](../research/swan-license-paths.md)

# FORGE Catalog — Current Integrated Version (v8+)

> This is the canonical integrated catalog. Addenda from v6/v7/v8 have been normalized here.
> For historical versions see `docs/planning/catalog/`.

---

## 1. Program Definition

FORGE (Federated Orchestrated Reasoning and Generative Engineering) is a multi-agent AI system for engineering-grade design and analysis. It is:

- **Not a chatbot** — it is a traceable, verifiable engineering reasoning pipeline
- **Not a CAD tool** — it wraps and orchestrates existing solvers (FEA, CFD, topology optimization)
- **Not a data lake** — it is a reasoning memory system with provenance, contradiction handling, and decay detection

### Core Properties

1. All results are traceable to sources with provenance
2. All claims pass the verification stack before entering the vault
3. All memory is persistent, contradiction-aware, and decay-detectable
4. All agent reasoning is recorded and retrievable
5. All tool invocations go through MCP wrapper contracts

---

## 2. System Components

### 2.1 Core Runtime (forge-core)

C++ orchestration spine. Responsibilities:
- Task intake, trace ID assignment, task classification
- Model routing with provider health monitoring and fallback
- Blackboard (typed, concurrent-safe, schema-validated shared state)
- Orchestrator (task graph, dependency DAG, specialist dispatch, escalation)
- A2A transport (gRPC production, local shim for testing)
- MCP client (tool invocation, result envelope parsing)
- Verification orchestration
- JSONL logging with trace context and metrics

### 2.2 Agent System (forge-agents)

Specialists, antagonists, verifiers, librarian, prompt engineer. Each agent has:
- A versioned prompt (semver, with CHANGELOG)
- An agent card (YAML: name, role, capabilities, tools, output contract ref)
- Prompt tests (expected behavior assertions)

**Specialist roster:** ME, Materials, EE, Plasma, Magnetics, Controls, Thermal/Fluids, Acoustics, Safety/SE, Biomedical
**Mathematician roster:** Optimization, PDE, Numerical, Symbolic, Geometry, Probability/Stats
**Verifier roster:** Structural, Adversarial, Provenance, Contradiction, Confidence Calibration

### 2.3 Memory System (forge-memory)

Obsidian-backed neural memory. Capabilities:
- Intake with schema validation
- Retrieval routing with context filtering and pathway strength
- Gap detection and deduplication
- Evidence strengthening and confidence updates
- Contradiction detection, versioning, and flagging
- Synthesis note generation from knowledge clusters
- Decay detection (no auto-delete — review flags only)
- Agent thinking catalog (reasoning records)
- ILC (Inter-domain Link Candidate) detection (V1)
- Emergent agent synthesis proposals (R&D, human approval gate)

### 2.4 Tooling Layer (forge-tools)

MCP wrappers for all external solvers. Each wrapper has:
- README
- WRAPPER_SPEC.md (behavior contract)
- INPUT_SCHEMA.md (typed input contract)
- OUTPUT_SCHEMA.md (typed output contract)
- ERRORS.md (error codes and handling)
- FIXTURES.md (test fixtures and golden outputs)

### 2.5 Verification Layer (forge-verification)

The trust boundary. Every agent output passes through:
1. Contract Gate — required fields, types, versions
2. Unit Gate — units present, normalized, internally consistent
3. Dimensional Gate — equation dimensionality checks
4. Provenance Gate — sources parseable, specific, not fabricated
5. Contradiction Gate — vault lookup for conflicting claims (V1 at MVP)
6. Assumption Gate — hidden assumptions disclosed
7. Adversarial Falsification — failure mode challenges
8. Confidence Calibration — evidence quality scoring

### 2.6 Data Contracts

All inter-component data is governed by versioned contracts. See `docs/contracts/`.

| Contract | Version | Status |
|---|---|---|
| Blackboard Schema | v1 | FROZEN |
| Agent Output Contract | v1 | FROZEN |
| MCP Wrapper Envelope | v1 | FROZEN |
| Vault Frontmatter Schema | v1 | FROZEN |
| Trace ID Standard | v1 | FROZEN |
| Error Codes | v1 | FROZEN |

---

## 3. Active Projects

### 3.1 Aladdin-3B

Smart fuselage / unmanned aircraft. MVP focus: motor mount bracket structural analysis.

Pipeline: Requirements → Decomposition → ME Specialist → GMSH → CalculiX → Verification → Vault

### 3.2 Project Vanguard

Structural/mechanism subassembly. Controls/ME/Materials interaction. V1: Gazebo + Newton + PhysX + digital twin.

### 3.3 Phoenix Nigredo Dracenix

Morphing configuration aircraft. Plasma/magnetics interactions. V1: OpenVSP + JSBSim + topology optimization (Swan preferred, FreeTO fallback).

---

## 4. Build Lane Priorities

| Lane | P-Tag | Lane Scope |
|---|---|---|
| A — Planning Canon | P0 | Freeze before build |
| B — Core Runtime Spine | P0 | First build target |
| C — Memory Core | P0 | First build target |
| D — Agents & Debate | P1 | Finalize during build |
| E — Tool Wrappers | P0 (MVP tools) | MVP critical path |
| F — Verification | P0 | MVP critical path |
| G — Tests & Red-Team | P0 (fixtures) | Must exist before build |
| H — Ops/Observability | P1 | Finalize during build |
| I — Project Pipelines | P1 | After core verified |
| J — R&D | P2 | Future |

---

## 5. Catalog Version History

| Version | Summary |
|---|---|
| v6 | Original FORGE architecture definition |
| v7 | Gap closure: antagonist system, ILC, RTSA scaffold |
| v8 | Execution addendum: build lanes, P0/P1/P2 tagging, planning cut line |
| v8+ (current) | Normalized integrated version (this document) |

See `docs/planning/catalog/` for historical versions.

# FORGE Catalog v0.1.0 (MVP)

| Field          | Value                                            |
|----------------|--------------------------------------------------|
| Classification | Python MVP · 7 Agents · 3 Providers             |
| Last Updated   | 2026-03-04                                       |
| Status         | ACTIVE — Planning Freeze in effect               |
| Supersedes     | All prior catalog fragments in `docs/planning/catalog/` |

---

## 1. Doctrine Principles

The FORGE project operates under 16 doctrine principles. Every design decision,
code review, and architecture choice must be traceable to at least one principle.

| #  | Principle                        | Summary |
|----|----------------------------------|---------|
| 1  | Epistemic Humility               | Acknowledge uncertainty in all engineering outputs. Confidence scores are mandatory; never claim certainty the models cannot justify. |
| 2  | Adversarial Verification         | Every analysis must survive adversarial challenge. The adversarial verifier exists to falsify, not confirm. |
| 3  | Knowledge Persistence            | Engineering knowledge must outlive individual sessions. The vault is the single source of truth. |
| 4  | Multi-Model Orchestration        | No single model owns the answer. Orchestrate specialist models and cross-verify outputs. |
| 5  | Engineering Rigor                | Dimensional analysis, unit consistency, and physical plausibility are non-negotiable. |
| 6  | Graceful Degradation             | The system must function when components fail. Supermemory down → Obsidian-only mode. Provider down → fallback chain. |
| 7  | Cost Awareness                   | Every API call has a cost. Budget gates prevent runaway spend. Cheaper models for cheaper tasks. |
| 8  | Transparent Reasoning            | Chain-of-thought must be logged and auditable. No black-box conclusions. |
| 9  | Continuous Learning              | Each analysis enriches the vault. Gap flags drive future knowledge acquisition. |
| 10 | Learn from DARK_leaf v2's Disorder | The predecessor project lost 29 rubric points to planning chaos, scope creep, and untested assumptions. Never repeat. |
| 11 | MVP Scope Lock                   | 7 agents, not 68. Ship what works. The remaining 61 are archived for V1. |
| 12 | Python First                     | C++ port only if Python latency fails validation targets. Premature optimization is the root of all evil. |
| 13 | Evidence Over Assumptions        | Every architectural choice must be backed by data or a validation experiment, not intuition. |
| 14 | Planning Freeze Protocol         | After the master index is accepted, no new planning documents. Code only. |
| 15 | Honest Estimation                | Pad estimates by 1.5×. If a task feels like 2 days, budget 3. |
| 16 | Rubric Rewards Building, Not Planning | Points come from working code, tested agents, and validated outputs — not from documents. |

---

## 2. Architecture Overview

### 2.1 Pipeline

The MVP architecture follows a linear pipeline with feedback loops:

```
┌────────────┐    ┌──────────────┐    ┌────────────┐    ┌───────────┐
│ Orchestrator│───▶│ Specialists  │───▶│ Verifiers  │───▶│ Librarian │
│  (ORCH-01) │    │ (E-01, E-05) │    │(V-STRUCT,  │    │ (LIB-01)  │
│             │◀───│              │◀───│  V-ADV)    │◀───│           │
└────────────┘    └──────────────┘    └────────────┘    └───────────┘
                                                              │
                                                              ▼
                                                        ┌───────────┐
                                                        │   Vault   │
                                                        └───────────┘
```

### 2.2 Blackboard Pattern

Inter-agent communication uses a **blackboard** (typed dictionary store):

- Agents read from and write to named slots on the blackboard.
- The orchestrator controls turn order; agents never communicate directly.
- Slot types are validated at write time to prevent schema drift.
- The blackboard is ephemeral per run; persistent state goes to the vault.

### 2.3 DAG-Based Task Decomposition

The orchestrator decomposes each user query into a **directed acyclic graph** (DAG):

1. Parse the engineering question into sub-tasks.
2. Identify dependencies between sub-tasks.
3. Assign each sub-task to the appropriate specialist agent.
4. Execute in topological order, parallelizing independent branches.
5. Merge results at convergence points.

### 2.4 The 12-Step Loop

Every analysis request follows this loop:

| Step | Action                          | Agent(s)         |
|------|---------------------------------|------------------|
| 1    | Receive user query              | Orchestrator     |
| 2    | Vault context assembly          | Librarian        |
| 3    | Task decomposition (DAG)        | Orchestrator     |
| 4    | Dispatch to specialists         | Orchestrator     |
| 5    | Specialist analysis             | E-01 / E-05     |
| 6    | Structural verification (T=0.0) | V-STRUCT         |
| 7    | Adversarial verification (T=0.3)| V-ADV            |
| 8    | Confidence scoring              | V-STRUCT + V-ADV |
| 9    | Result synthesis                | Orchestrator     |
| 10   | Vault persistence               | Librarian        |
| 11   | Gap detection & flagging        | Librarian        |
| 12   | Return response to user         | Orchestrator     |

---

## 3. AI Provider Fleet

### 3.1 Provider Table

| Provider  | Model              | Tier     | Roles                                          | Status    |
|-----------|--------------------|----------|-------------------------------------------------|-----------|
| Anthropic | claude-opus-4-6      | Frontier | Orchestrator, Materials Specialist, Struct. Ver. | Active    |
| Anthropic | claude-sonnet-4-5  | Mid      | Librarian, Pipeline Tester                      | Active    |
| OpenAI    | gpt-5.2            | Frontier | ME Specialist, Adversarial Verifier             | Active    |
| DeepSeek  | deepseek-reasoner  | Mid      | Cost-saving backup                              | Pending   |

### 3.2 Notes

- **DeepSeek** is pending Week 2 validation experiment. It will be evaluated
  for reasoning quality on standard structural problems before promotion.
- **Doubao** (ByteDance) was considered but deferred to V1 (see ADR-006).
- Fallback chain: If a provider is unreachable, the router attempts the next
  provider in the same tier. If no same-tier provider is available, it
  degrades to mid-tier.

### 3.3 Budget Controls

- Daily ceiling: TBD after Week 1 cost validation experiment.
- Alert threshold: 80% of daily ceiling triggers a warning.
- Hard stop: 100% of ceiling halts all non-essential API calls.

---

## 4. MVP Agent Roster

### 4.1 Agent Table

| ID       | Name                  | Role                                                    | Provider  | Model             |
|----------|-----------------------|---------------------------------------------------------|-----------|--------------------|
| ORCH-01  | Orchestrator          | Task decomposition, DAG construction, dispatch, 12-step loop | Anthropic | claude-opus-4-6      |
| E-01     | ME Specialist         | Structural/mechanical analysis, FEA setup, stress calcs | OpenAI    | gpt-5.2            |
| E-05     | Materials Specialist  | Material selection, properties, degradation. ME Antagonist | Anthropic | claude-opus-4-6      |
| V-STRUCT | Structural Verifier   | Contract enforcement (T=0.0), unit checks, dim. analysis | Anthropic | claude-opus-4-6      |
| V-ADV    | Adversarial Verifier  | Falsification attempts (T=0.3), plausibility bounds     | OpenAI    | gpt-5.2            |
| LIB-01   | Librarian             | Vault read/write, context assembly, gap detection       | Anthropic | claude-sonnet-4-5  |
| TEST-01  | Pipeline Tester       | End-to-end validation, golden fixture comparison        | Anthropic | claude-sonnet-4-5  |

### 4.2 Domain Summaries

- **ORCH-01 — Orchestrator**: Owns the control loop. Decomposes problems, builds
  the DAG, dispatches work, and synthesizes final answers. Does not perform
  engineering analysis itself.

- **E-01 — ME Specialist**: The primary engineering brain. Handles stress
  analysis, beam deflection, fatigue life, FEA problem setup, and boundary
  condition specification. Vault domain: `vault/domains/mechanical/`.

- **E-05 — Materials Specialist**: Selects materials, retrieves properties
  (yield strength, fatigue limits, corrosion resistance), and models
  degradation. Also serves as the ME Antagonist — challenges E-01's assumptions.
  Vault domain: `vault/domains/materials/`.

- **V-STRUCT — Structural Verifier**: Zero-temperature verification. Checks
  dimensional consistency, unit correctness, and contract compliance. Rejects
  any output missing mandatory fields.

- **V-ADV — Adversarial Verifier**: Elevated-temperature verification (T=0.3).
  Actively tries to break the analysis — finds edge cases, challenges
  assumptions, tests boundary conditions.

- **LIB-01 — Librarian**: Manages the Obsidian vault. Reads prior analyses for
  context, writes new results, detects knowledge gaps, and maintains the
  note schema.

- **TEST-01 — Pipeline Tester**: Runs golden-fixture tests against known
  engineering problems with textbook answers. Validates end-to-end pipeline
  correctness and catches regressions.

### 4.3 Archived Agents

61 additional agents were designed during the DARK_leaf v2 era. They are
archived in `docs/planning/catalog/` and will be evaluated for V1 promotion
based on MVP learnings. See Doctrine Principle #11: MVP Scope Lock.

---

## 5. Toolchain

### 5.1 MVP Tools

| ID   | Tool      | Purpose                | Target Milestone | Status  |
|------|-----------|------------------------|------------------|---------|
| T-01 | CalculiX  | Structural FEA solver  | M6               | Planned |
| T-06 | GMSH      | Mesh generation        | M6               | Planned |

### 5.2 Tool Integration Pattern

Tools are wrapped as Python modules in `src/forge/tools/`. Each wrapper:

1. Validates input parameters against a schema.
2. Writes input files to a temporary directory.
3. Invokes the tool as a subprocess.
4. Parses output files into structured Python objects.
5. Logs invocation metadata (duration, exit code, input hash).

### 5.3 Deferred Tools

- **FreeTO** (topology optimization): Deferred to V1. Requires Swan license
  resolution (see ADR-005).
- **Custom solvers**: Any additional solvers will be evaluated after M6 tool
  validation is complete.

---

## 6. Memory Architecture

### 6.1 Operating Modes

| Mode     | Components              | When                              |
|----------|-------------------------|-----------------------------------|
| Full     | Obsidian + Supermemory  | Supermemory API available & valid  |
| Degraded | Obsidian only           | Default MVP mode                  |

In degraded mode, all memory operations use the local Obsidian vault. The
Librarian agent handles read/write. Supermemory integration was attempted
during M2 and is not required for the MVP gate.

### 6.2 Vault Layout

```
vault/
├── domains/
│   ├── mechanical/          # ME domain knowledge
│   │   ├── beam_theory.md
│   │   ├── stress_analysis.md
│   │   └── fatigue.md
│   ├── materials/           # Material properties & selection
│   │   ├── steel_alloys.md
│   │   ├── aluminum_alloys.md
│   │   └── composites.md
│   └── thermal/             # Thermal analysis (V1 scope)
├── analyses/
│   ├── YYYY-MM-DD_<slug>/   # One directory per analysis run
│   │   ├── input.md         # Original query + context
│   │   ├── output.md        # Final synthesized answer
│   │   ├── dag.json         # Task decomposition graph
│   │   └── verification.md  # Verifier reports
│   └── index.md             # Analysis registry
└── validation/
    ├── golden_fixtures/     # Known-answer test cases
    └── regression_log.md    # Regression test history
```

### 6.3 Note Schema

Every vault note uses YAML frontmatter with these fields:

```yaml
---
title: "Note Title"
domain: "mechanical | materials | thermal | general"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
confidence: 0.0-1.0          # Epistemic confidence in content
sources:                      # Provenance tracking
  - "textbook:Shigley:Ch4"
  - "analysis:2026-03-01_beam_deflection"
gap_flags:                    # Knowledge gaps detected
  - "Missing fatigue data for Ti-6Al-4V at elevated temperature"
tags:
  - mechanical
  - stress-analysis
---
```

### 6.4 Gap Detection

The Librarian scans vault notes for `gap_flags` entries. Gaps are:

- Surfaced to the user as "known unknowns" in analysis responses.
- Logged in `vault/validation/regression_log.md` for tracking.
- Prioritized for future knowledge acquisition sessions.

---

## 7. Quality Contracts

### 7.1 Mandatory Output Fields

Every engineering analysis output must include these 11 fields:

| #  | Field                | Type    | Description                                    |
|----|----------------------|---------|------------------------------------------------|
| 1  | `analysis_id`        | string  | Unique identifier (UUID v4)                    |
| 2  | `timestamp`          | ISO8601 | When the analysis completed                    |
| 3  | `query`              | string  | Original user question                         |
| 4  | `methodology`        | string  | Analytical approach used                       |
| 5  | `assumptions`        | list    | Explicit assumptions made                      |
| 6  | `results`            | object  | Numerical results with units                   |
| 7  | `units`              | object  | Unit specification for all quantities           |
| 8  | `confidence`         | float   | Overall confidence score (0.0–1.0)             |
| 9  | `verification_status`| string  | "passed" / "failed" / "partial"                |
| 10 | `sources`            | list    | References and provenance                      |
| 11 | `caveats`            | list    | Limitations and known gaps                     |

### 7.2 Confidence Scoring

Confidence is computed as the minimum of:

- **Structural verification score**: Binary pass/fail on unit and dimensional checks.
- **Adversarial verification score**: Graduated 0.0–1.0 based on how many
  falsification attempts the analysis survives.
- **Source confidence**: Based on provenance quality (textbook > paper > estimate).

### 7.3 Verification Pipeline

| Stage                 | Agent    | Temperature | Criteria                              |
|-----------------------|----------|-------------|---------------------------------------|
| Structural Verification | V-STRUCT | T = 0.0   | Units correct, dimensions consistent, mandatory fields present, physical plausibility |
| Adversarial Verification | V-ADV  | T = 0.3   | Survives edge-case challenges, assumption stress-testing, boundary condition probing |

An analysis must pass structural verification to be returned. Adversarial
verification failures reduce confidence but do not block output (the caveats
field captures concerns).

---

## 8. Vault Layout Reference

Complete directory tree for the vault:

```
vault/
├── domains/
│   ├── mechanical/
│   │   ├── beam_theory.md
│   │   ├── stress_analysis.md
│   │   ├── fatigue.md
│   │   ├── buckling.md
│   │   └── connections.md
│   ├── materials/
│   │   ├── steel_alloys.md
│   │   ├── aluminum_alloys.md
│   │   ├── composites.md
│   │   ├── material_selection_criteria.md
│   │   └── degradation_models.md
│   └── thermal/               # Placeholder — V1 scope
│       └── _README.md
├── analyses/
│   ├── index.md               # Master registry of all analyses
│   └── YYYY-MM-DD_<slug>/     # Per-analysis directories
│       ├── input.md
│       ├── output.md
│       ├── dag.json
│       └── verification.md
└── validation/
    ├── golden_fixtures/
    │   ├── cantilever_beam.yaml
    │   ├── simply_supported_beam.yaml
    │   └── axial_stress.yaml
    └── regression_log.md
```

---

## Appendix A: Cross-References

| Document                  | Path                              | Purpose                    |
|---------------------------|-----------------------------------|----------------------------|
| FORGE Catalog (this doc)  | `docs/planning/FORGE_CATALOG.md`  | Architecture & roster      |
| Execution Plan            | `docs/planning/FORGE_EXECUTION_PLAN.md` | Timeline & process   |
| Decision Log              | `docs/planning/DECISIONS.md`      | ADRs                       |
| Configuration             | `forge.yaml`                      | Runtime config             |
| Changelog                 | `CHANGELOG.md`                    | Version history            |

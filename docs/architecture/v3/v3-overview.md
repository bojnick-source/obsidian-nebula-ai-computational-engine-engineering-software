# FORGE v3 Architecture Extension

> Extends the v1/v2 planning scaffold with two new architectural layers: the four-context output presentation system and the unified learning loop.

---

## What v3 Adds

| Layer | Description |
|---|---|
| **forge-output** | Four output contexts sharing one JSONL event bus: live TUI, deliverable reports, vault write-back, monitoring |
| **forge-learning** | Unified learning loop: episodic memory, external knowledge discovery, engineering constitution, adversarial debate protocol |

---

## Design Principles (v3)

1. **One event bus, four consumers.** The C++ core writes append-only JSONL to a ZeroMQ PUB socket. All downstream presentation and learning systems subscribe — no direct coupling between core and consumers.

2. **The quality evaluator is the gatekeeper.** Strict selective memory addition gated by an LLM-as-judge (Engineering Constitution rules) yields self-improvement. Add-all degrades performance. This is the single most critical v3 architectural decision.

3. **Computable checks are never debated.** Conservation laws, energy balance, mesh convergence — these are deterministic Python functions. They never enter the LLM debate protocol. Errors caught here cost tokens; errors passed through cost engineering validity.

4. **Obsidian vault as dual-interface memory.** Human-browsable via Graph View + Dataview. Agent-retrievable via Supermemory sub-300ms hybrid search. One knowledge base, two access patterns.

5. **Temporal for crash-resistant durable execution.** Every step in a long FEA/CFD run is checkpointed. Human-in-the-loop gates pause on confidence drops.

---

## Component Map

```
FORGE v3 Architecture

┌─────────────────────────────────────────────────────────────────┐
│                     C++ CORE (forge-core)                       │
│  ┌─────────────┐   ┌───────────┐   ┌───────────────────────┐   │
│  │ Orchestrator│──▶│ Blackboard│   │ OpenTelemetry C++ SDK │   │
│  └─────────────┘   └───────────┘   └───────────────────────┘   │
│           │                                                      │
│           ▼ ZeroMQ PUB                                          │
│  ┌─────────────────────┐                                        │
│  │  JSONL Event Stream │ (forge/events/v1 schema)               │
│  └──────────┬──────────┘                                        │
└─────────────┼───────────────────────────────────────────────────┘
              │ ZeroMQ SUB (fan-out)
    ┌─────────┴──────────────────────────────────┐
    │                                            │
    ▼                                            ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│       forge-output           │    │       forge-learning          │
│                              │    │                              │
│  1A: Textual TUI             │    │  2A: Episodic Memory         │
│  1B: Report Generator        │    │  2B: Knowledge Discovery     │
│      (Jinja2+WeasyPrint)     │    │  2C: Engineering Constitution│
│  1C: Vault Write-Back        │    │      + Debate Protocol       │
│      (python-frontmatter     │    │  2D: Temporal Learning Loop  │
│       + Supermemory)         │    │                              │
│  1D: Monitoring              │    │  Quality Evaluator (gatekeeper)│
│      (DuckDB+structlog)      │    │  Agent Skill Library         │
└──────────────────────────────┘    └──────────────────────────────┘
```

---

## Build Order (v3)

Following incremental build philosophy:

| Week | Deliverable |
|---|---|
| 1 | JSONL event schema + ZMQ event emitter + structlog + Rich TUI prototype + python-frontmatter vault writes |
| 2 | Textual TUI (full) + DuckDB log analysis + Dataview vault queries |
| 3 | Coolify deployment + Supermemory integration + post-run capture schema |
| 4 (month 2) | Temporal workflows + quality evaluator + Engineering Constitution |
| 5 (month 3) | External knowledge discovery + full adversarial debate protocol |

---

## Reference Documents

- [Event Bus Architecture](event-bus.md)
- [Textual TUI Spec](tui-spec.md)
- [Report Generation Pipeline](report-generation.md)
- [Vault Write-Back Design](vault-writeback.md)
- [Monitoring Architecture](monitoring-architecture.md)
- [Memory Hierarchy](memory-hierarchy.md)
- [Episodic Memory System](episodic-memory.md)
- [Knowledge Discovery](knowledge-discovery.md)
- [Engineering Constitution](engineering-constitution.md)
- [Adversarial Debate Protocol](adversarial-debate-protocol.md)
- [Temporal Learning Loop](temporal-learning-loop.md)
- [Agent Leveling System](agent-leveling-system.md)

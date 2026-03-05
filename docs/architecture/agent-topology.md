# Agent Topology

> Roles, relationships, and dispatch rules for the FORGE agent system.

---

## Agent Hierarchy

```
ORCHESTRATOR
│
├── LIBRARIAN (memory interface — called before and after specialist phase)
│
├── SPECIALISTS (domain experts — one dispatched per task)
│   ├── ME (Mechanical Engineering)
│   ├── Materials
│   ├── EE (Electrical Engineering)
│   ├── Plasma
│   ├── Magnetics
│   ├── Controls
│   ├── Thermal/Fluids
│   ├── Acoustics
│   ├── Safety/SE
│   └── Biomedical
│
├── MATHEMATICIANS (invoked by specialists or orchestrator for math-heavy sub-tasks)
│   ├── Optimization
│   ├── PDE
│   ├── Numerical
│   ├── Symbolic
│   ├── Geometry
│   └── Probability/Stats
│
├── ANTAGONISTS (paired with specialists — V1, full mode only)
│   ├── ME Antagonist
│   ├── Materials Antagonist
│   └── (other domain antagonists)
│
├── VERIFIERS (called after every specialist + tool output)
│   ├── Structural Verifier
│   ├── Adversarial Verifier  [V1]
│   ├── Provenance Verifier
│   ├── Contradiction Gate  [V1]
│   └── Confidence Calibration  [V1]
│
└── PROMPT ENGINEER (meta — not in task loop; manages prompt registry)
```

---

## Dispatch Rules

| Trigger | Agent Dispatched |
|---|---|
| Task classified as structural analysis | ME Specialist |
| Task classified as materials selection | Materials Specialist |
| Task involves multi-physics | ME + relevant domain specialists in sequence |
| Post-specialist output | Librarian (memory write), Verifiers |
| Post-tool output | Structural Verifier, Provenance Gate |
| V1: Full mode | Antagonist paired with primary specialist |

---

## Agent Card Schema

Each agent has a card in `forge-agents/registry/agent_cards/`:

```yaml
id: me_specialist
name: Mechanical Engineering Specialist
version: "1.0.0"
role: specialist
domain: mechanical_engineering
capabilities:
  - structural_analysis
  - stress_strain
  - fatigue
  - vibration
  - thermal_mechanical
tools_allowed:
  - gmsh
  - calculix
output_contract_ref: docs/contracts/agent-output-contract.md
prompt_ref: forge-agents/prompts/me_specialist/v1.0.0.md
antagonist_pair: materials_antagonist
```

---

## A2A Protocol (V1)

Agent-to-agent communication uses the A2A protocol. At MVP, specialists are called sequentially without debate. V1 adds:

- Debate lifecycle (see `docs/architecture/mcp-a2a-boundaries.md`)
- gRPC transport for production
- Local shim for testing

---

## Leveling Policy

See `forge-agents/docs/agent-leveling.md` for how agents are promoted, tested, and versioned.

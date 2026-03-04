# FORGE — AI Computational Engine for Engineering Software

FORGE is a multi-agent AI system for computational engineering analysis. It
orchestrates specialist LLM agents to perform structural analysis, material
selection, and verification — with adversarial checking, confidence scoring,
and persistent knowledge management via an Obsidian vault. The MVP targets
mechanical engineering with 7 agents across 3 AI providers (Anthropic, OpenAI,
DeepSeek).

## Quick Start

```bash
# Install in development mode
pip install -e ".[dev]"

# Verify installation
forge --version
# FORGE v0.1.0 (MVP)

# Run the smoke test
forge --smoke-test

# Run the full test suite
pytest tests/ -q
```

## Project Status

| Field           | Value                                    |
|-----------------|------------------------------------------|
| Version         | 0.1.0 (MVP)                             |
| Phase           | Phase 0.1 complete — foundation shipped  |
| Planning Freeze | **In effect** — code only from here      |
| Agents          | 7 of 68 (61 archived for V1)            |
| Providers       | Anthropic, OpenAI, DeepSeek (pending)    |
| Memory Mode     | Degraded (Obsidian only)                 |

## Directory Structure

```
forge/
├── README.md
├── CHANGELOG.md
├── forge.yaml                  # Runtime configuration
├── pyproject.toml              # Python project metadata
├── src/forge/
│   ├── __init__.py
│   ├── cli.py                  # CLI entry point
│   ├── config.py               # YAML config loader
│   ├── logging.py              # JSONL structured logging
│   ├── blackboard.py           # Inter-agent communication store
│   ├── model_router.py         # Provider selection & fallback
│   ├── agents/                 # Agent runtime modules
│   ├── memory/                 # Vault & Supermemory integration
│   ├── router/                 # Routing logic
│   └── tools/                  # Tool wrappers (CalculiX, GMSH)
├── agents/
│   ├── orchestrator/           # SKILL.yaml, prompt.md, CHANGELOG.md
│   ├── me_specialist/
│   ├── materials_specialist/
│   ├── structural_verifier/
│   ├── adversarial_verifier/
│   ├── librarian/
│   └── pipeline_tester/
├── tests/                      # pytest test suite
├── docs/planning/
│   ├── FORGE_CATALOG.md        # Architecture & agent roster
│   ├── FORGE_EXECUTION_PLAN.md # Timeline & process
│   ├── DECISIONS.md            # Architectural decision records
│   └── catalog/                # Archived pre-consolidation docs
├── logs/                       # JSONL log output
└── vault/                      # Obsidian knowledge vault
    ├── domains/                # Engineering domain knowledge
    ├── analyses/               # Per-analysis results
    └── validation/             # Golden fixtures & regression logs
```

## MVP Agent Roster

| ID       | Name                  | Role                                        | Provider  | Model             |
|----------|-----------------------|---------------------------------------------|-----------|--------------------|
| ORCH-01  | Orchestrator          | Task decomposition, DAG construction, 12-step loop | Anthropic | claude-opus-4-6 |
| E-01     | ME Specialist         | Structural/mechanical analysis, FEA setup    | OpenAI    | gpt-5.2            |
| E-05     | Materials Specialist  | Material selection, properties, ME Antagonist | Anthropic | claude-opus-4-6 |
| V-STRUCT | Structural Verifier   | Contract enforcement (T=0.0), unit checks    | Anthropic | claude-opus-4-6 |
| V-ADV    | Adversarial Verifier  | Falsification attempts (T=0.3), bounds check | OpenAI    | gpt-5.2            |
| LIB-01   | Librarian             | Vault read/write, context assembly, gap detection | Anthropic | claude-sonnet-4-5 |
| TEST-01  | Pipeline Tester       | End-to-end validation, golden fixtures       | Anthropic | claude-sonnet-4-5 |

## Planning Documents

| Document               | Description                           |
|------------------------|---------------------------------------|
| [FORGE Catalog](docs/planning/FORGE_CATALOG.md) | Architecture, agent roster, toolchain, memory, quality contracts |
| [Execution Plan](docs/planning/FORGE_EXECUTION_PLAN.md) | Timeline, rubric, risk register, session checklists |
| [Decisions (ADR)](docs/planning/DECISIONS.md) | Architectural decision records (ADR-001 through ADR-007) |

## Development

```bash
# Run tests
pytest tests/ -q

# Run tests with coverage
pytest tests/ --cov=src/forge

# Lint
ruff check src/ tests/

# Type check
mypy src/forge/
```

## License

MIT
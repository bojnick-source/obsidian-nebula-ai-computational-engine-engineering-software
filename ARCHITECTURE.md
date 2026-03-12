# FORGE Architecture — Two-Layer Design

## The Two Layers

FORGE uses a deliberate two-layer architecture. Understanding the naming convention
prevents the most common source of confusion:

| Directory | Type | Purpose |
|---|---|---|
| `forge-agents/` | **Data Layer** (hyphen) | Agent declarations, SKILL.md files, learned data |
| `forge_agent/` | **Runtime Layer** (underscore) | Python package — orchestration, routing, MCP |

They are **separate concerns**. Neither is a copy or duplicate of the other.

---

## `forge-agents/` — The Data Layer

```
forge-agents/
├── {agent_id}/              # One directory per agent (212+ agents)
│   ├── SKILL.md             # Skill declaration: role, tools, constraints, examples
│   ├── learned/             # Accumulated operational knowledge
│   │   ├── tool_prefs.yaml          # Which tools work best for this agent
│   │   ├── failure_patterns.jsonl   # Recorded failure modes
│   │   └── strategies.jsonl         # Successful strategies
│   ├── gold_runs/           # Exemplary interaction records
│   │   ├── README.md
│   │   └── example_01.md
│   └── catalogue.md         # Agent capability catalogue
├── catalogues/              # Cross-agent domain catalogues (aggregated)
├── prompts/                 # Prompt templates per agent
├── prompt_tests/            # Structured tests for prompt correctness
└── registry/               # agent_registry.yaml, antagonist_pairs.yaml
```

**Key properties:**
- No Python. Pure data and markdown.
- Declarative: describes what an agent knows and does, not how it runs.
- Runtime-independent: can be inspected, validated, and updated without touching Python.
- Validated by `tools/validate_registry.py` (CI-enforced).

---

## `forge_agent/` — The Runtime Layer

```
forge_agent/
├── core/                    # Routing, governance, token budget, MCP manager
│   ├── intelligence_router.py   # Classifies tasks → picks specialist
│   ├── unified_agent.py         # Top-level async agent loop
│   ├── governance.py            # Role-based access control
│   ├── mcp_manager.py           # MCP server lifecycle management
│   └── ...
├── core/                    # Infrastructure (routing, governance, orchestration)
│   ├── multi_agent_orchestrator.py  # v2 orchestrator (XML parsing, dep graph, vault persistence)
│   ├── orchestrator_v1_deprecated.py # v1 legacy — kept for reference only
│   ├── verifier.py              # Quality gate (verifies agent output contracts)
│   ├── intelligence_router.py   # Classifies tasks → picks specialist
│   ├── unified_agent.py         # Top-level async agent loop
│   ├── governance.py            # Role-based access control
│   ├── mcp_manager.py           # MCP server lifecycle management
│   └── ...
├── agents/                  # Domain agent persona modules (prompt constants only)
│   ├── domain_specialists/      # Cross-cutting specializations (acoustics, controls, materials,
│   │                            #   plasma, systems, thermal_fluids)
│   ├── engineers/               # Engineering domain agents (mechanical_engineer,
│   │                            #   electrical_engineer, biomedical, propulsion, robotics, …)
│   ├── mathematicians/          # Mathematics domain specialists
│   ├── physicists/              # Physics domain specialists
│   └── specialists/             # Redirect shims only — all content moved to engineers/ or
│                                #   domain_specialists/ (kept for backwards compatibility)
├── memory/                  # Obsidian vault integration (MCP server)
│   ├── obsidian_manager.py      # Vault CRUD + TF-IDF search
│   └── obsidian_mcp_server.py   # FastMCP server exposing vault tools
├── config/                  # YAML configuration files
└── tests/                   # Unit/integration tests for runtime
```

**Key properties:**
- Python package (`pip install -e forge_agent/`).
- Implements the 9-phase core loop (intake → routing → decomposition → memory preflight
  → specialist → tool execution → verification → persistence → output).
- Uses `forge-agents/` data at runtime: reads SKILL.md to build agent context, reads
  `learned/tool_prefs.yaml` to weight tool selection.

---

## Other Forge Modules

```
forge-assembly/     # Python: CAD assembly pipeline (placement, mass props, DFA)
forge-output/       # Python: Report and artifact generation
forge-core/         # C++: High-performance blackboard, routing, MCP bindings
forge-learning/     # Learning infrastructure (temporal loops, feedback)
forge-memory/       # Memory system extensions
forge-vault/        # Vault storage backends
forge-verification/ # Standalone verification tools
forge-tests/        # Integration test harness
forge-tools/        # CLI and utility scripts
```

---

## How the Layers Interact

```
                    ┌─────────────────────────────────┐
                    │        forge-agents/ (data)      │
                    │   SKILL.md  learned/  catalogue  │
                    └──────────────┬──────────────────┘
                                   │  read at runtime
                    ┌──────────────▼──────────────────┐
                    │      forge_agent/ (runtime)      │
                    │  intelligence_router → specialist │
                    │  orchestrator → mcp_manager       │
                    │  obsidian_manager → vault         │
                    └──────────────┬──────────────────┘
                                   │  calls
                    ┌──────────────▼──────────────────┐
                    │  forge-assembly / forge-output   │
                    │  (domain Python packages)        │
                    └─────────────────────────────────┘
```

---

## Adding a New Agent

1. Run the scaffold tool:
   ```sh
   python tools/scaffold_agent.py \
       --id my_new_specialist \
       --role specialist \
       --domain "My Domain" \
       --domain-short "my-domain" \
       --pair my_new_antagonist \
       --status planned
   ```
2. Edit `forge-agents/my_new_specialist/SKILL.md` (must have ≥ 60 lines, ≥ 8 `##` headings).
3. Add a Python persona in `forge_agent/agents/{category}/my_new.py`.
4. Run `python tools/validate_registry.py` to confirm registry integrity.
5. Add agent IDs to `registry/agent_registry.yaml`.

---

## Validating the Repository

```sh
yamllint .                           # YAML lint
ruff check . --ignore E501           # Python lint
python tools/validate_registry.py   # Registry integrity (all agent cards + SKILL.md)
pytest --tb=short -q                 # All tests
```

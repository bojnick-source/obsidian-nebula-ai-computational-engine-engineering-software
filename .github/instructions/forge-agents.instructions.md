---
applyTo: "forge-agents/**,forge_agent/agents/**"
---

# FORGE — Agent Development Instructions

## Two-Layer Agent System

Every FORGE agent exists in two places:

| Layer | Location | Contains |
|---|---|---|
| **Data** | `forge-agents/{agent_id}/` | `SKILL.md`, `catalogue.md`, `learned/tool_prefs.yaml` |
| **Runtime** | `forge_agent/agents/{category}/{agent_id}.py` | `ROLE`, `MODEL`, `TEMPERATURE`, `SYSTEM_PROMPT` |

These are kept deliberately separate. The data layer is runtime-independent (inspectable,
versionable). The runtime layer is pure Python prompt configuration.

## Creating a New Agent

Use the scaffold tool — never create agents manually:

```bash
python tools/scaffold_agent.py \
    --id my_new_specialist \
    --role specialist \
    --domain "My Domain — Description" \
    --domain-short "my_domain" \
    --pair my_new_antagonist \
    --status planned
```

This generates:
- `forge-agents/my_new_specialist/SKILL.md` (template, ≥60 lines, ≥8 `##` headings)
- `forge-agents/my_new_specialist/catalogue.md`
- `forge-agents/my_new_specialist/learned/tool_prefs.yaml`
- Entry in `forge-agents/registry/agent_registry.yaml`

After scaffolding, manually add the Python persona:
`forge_agent/agents/{category}/my_new_specialist.py`

## SKILL.md Requirements (CI-enforced)

- Minimum **60 lines**
- Minimum **8 `##` section headings**
- Must include: Capability Definition, Tools Allowed, Mandatory Output Fields,
  Output Contract, Learned Strategies, Known Failure Patterns, Level Progression,
  Escalation Flags

## Agent Naming Rules

- IDs: `snake_case` only
- Specialist suffix: `_specialist`
- Antagonist suffix: `_antagonist`
- Python filenames: full descriptive name — `mechanical_engineer.py` not `me.py`
- Python filenames must match the `ROLE` string they define

## Runtime Agent Directory Mapping

| Category | Directory | Examples |
|---|---|---|
| Engineering subdomains | `agents/domain_specialists/` | acoustics, controls, materials, plasma |
| Engineering disciplines | `agents/engineers/` | mechanical_engineer, electrical_engineer, propulsion |
| Mathematics | `agents/mathematicians/` | number_theory, pde, optimization |
| Physics | `agents/physicists/` | astrophysics, condensed_matter, quantum_field_theory |
| Infrastructure | `core/` | verifier, multi_agent_orchestrator — NOT in agents/ |

## Output Contract (Mandatory Fields)

Every specialist must return a JSON with these fields (defined in `docs/contracts/agent-output-contract.md`):

```json
{
  "model_choice": "rationale for engineering model chosen",
  "equations": ["LaTeX equation 1", "LaTeX equation 2"],
  "units": "all SI",
  "sanity_checks": ["limiting_case or conservation or dimensional"],
  "calculation_path": "step-by-step derivation",
  "findings": "...",
  "assumptions": "...",
  "what_would_falsify": "...",
  "provenance": "...",
  "confidence": 0.85
}
```

## Registry Validation

After any registry change:
```bash
python tools/validate_registry.py          # exit 0 = PASS
python tools/validate_registry.py --report # JSON detail
```

This is also enforced in CI (`validate-registry` job). A PR with registry validation
failure cannot merge.

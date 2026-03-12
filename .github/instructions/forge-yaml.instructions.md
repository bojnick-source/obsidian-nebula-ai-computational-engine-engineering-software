---
applyTo: "**/*.yaml,**/*.yml"
---

# FORGE — YAML Coding Instructions

## Agent Card Schema (forge-agents/registry/agent_cards/*.yaml)

Required fields in every agent card:
```yaml
id: agent_id_snake_case
name: "Human Readable Name"
version: "1.0.0"
role: specialist | antagonist | verifier | workflow | librarian | tester
domain: domain_slug
status: planned | mvp | v1 | v2

output_contract_ref: docs/contracts/agent-output-contract.md
skill_ref: forge-agents/{agent_id}/SKILL.md

antagonist_pair: paired_agent_id   # specialists only

mandatory_output_fields:
  - findings
  - assumptions
  - what_would_falsify
  - provenance
  - confidence
```

**Do NOT include:**
- `prompt_ref:` — this field is removed (pointed to a directory that never existed)
- `capabilities: []` — removed (empty; content lives in SKILL.md)
- `tools_allowed: []` — removed (empty; content lives in SKILL.md)

## List Indentation

All YAML list items use **2-space indent**:
```yaml
# CORRECT
mandatory_output_fields:
  - findings
  - assumptions

# WRONG — 4-space
mandatory_output_fields:
    - findings
    - assumptions
```

## Line Length

Max 120 characters. Break long shell strings in workflow run: blocks with `\`:
```yaml
run: |
  echo "first part of long message" \
    "continuation here"
```

## GitHub Actions Workflows

- The `on:` key is excluded from yamllint via `.yamllint.yml ignore: .github/workflows/`.
  Do not quote it as `"on":` — just leave it as `on:`.
- Never add `|| true` to lint/test steps in CI.

## Config File Ownership

| File | Owned By | Purpose |
|---|---|---|
| `forge_agent/config/forge.yaml` | Python runtime | Master runtime config (vault, providers, limits) |
| `forge-core/configs/forge.yaml` | C++ core | Simplified router subset for C++ |
| `forge_agent/config/model_router.yaml` | Python runtime | Role→provider→model tier mapping |
| `forge-core/configs/model_router.yaml` | C++ core | C++ router rules |
| `forge_agent/config/skill_server_map.yaml` | Python runtime | Skill→MCP server mapping |
| `forge-core/configs/skill_server_map.yaml` | C++ core | MCP tool server locations |
| `mesh-morph-lhs/config/design_space.yaml` | mesh-morph-lhs | LHS design parameters |

Do not sync configs across layers without updating both.

## Registry Files

- `forge-agents/registry/agent_registry.yaml` — canonical agent list (v2 schema)
- `forge-agents/registry/antagonist_pairs.yaml` — debate pairings
- Always run `python tools/validate_registry.py` after modifying either file.

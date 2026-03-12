# FORGE — Developer Quick Reference

## Setup

```sh
pip install pytest pytest-asyncio pyyaml ruff yamllint
pip install -e forge_agent/
pip install -e forge-assembly/
pip install -e forge-output/
```

## Run Tests

```sh
pytest --tb=short -q          # all tests
pytest tests/                 # smoke + regression tests only
pytest forge_agent/tests/     # forge_agent unit tests
pytest tools/tests/           # tools unit tests
```

## Lint

```sh
yamllint .                    # YAML lint (uses .yamllint.yml)
ruff check . --ignore E501    # Python lint
```

## Registry

```sh
python tools/validate_registry.py          # validate all 214 agents (exit 0 = PASS)
python tools/validate_registry.py --report # JSON report
```

## Generate Agent Scaffolds

```sh
# Single agent:
python tools/scaffold_agent.py \
    --id aerodynamics_specialist \
    --role specialist \
    --domain "Aerodynamics — Lift, Drag, Propulsion" \
    --domain-short "aerodynamics" \
    --pair aerodynamics_antagonist \
    --status planned

# Batch from manifest:
python tools/scaffold_agent.py --batch tools/agent_manifest.yaml
```

## Conventions

- Agent IDs: `snake_case`, suffix `_specialist` or `_antagonist`
- SKILL.md: minimum 60 lines, 8 `##` headings required (CI enforced)
- Agent cards: YAML list items must be 2-space indented (`  - item`)
- Branch pattern: `claude/<description>-<SESSION_ID>`
- Current dev branch: `claude/forge-planning-scaffold-WBFmM`

## CI Checks

All PRs run: yamllint → ruff → pytest. All three must pass (no `|| true`).
Registry validation is a separate tool, not yet in CI — run manually before PRs.

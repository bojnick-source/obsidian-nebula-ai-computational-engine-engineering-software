---
applyTo: "**"
---

# FORGE — General Project Instructions

## What This Project Is

FORGE is a multi-agent AI orchestration system for engineering analysis. It has a strict
two-layer architecture:

- `forge-agents/` (hyphen) = **Data layer** — YAML agent cards, SKILL.md files, registry
- `forge_agent/` (underscore) = **Runtime layer** — Python package, orchestration, MCP

Never confuse the two. The naming difference (hyphen vs underscore) is intentional and documented.

## Directory Layout (as of 2026-03-12 reorganization)

```
forge_agent/
├── core/          ← infrastructure: orchestrator (v2), verifier, governance, routing, MCP
├── agents/
│   ├── domain_specialists/   ← acoustics, controls, materials, plasma, systems, thermal_fluids
│   ├── engineers/            ← mechanical_engineer, electrical_engineer, biomedical, propulsion…
│   ├── mathematicians/       ← number_theory, pde, optimization, complex_analysis…
│   └── physicists/           ← astrophysics, quantum_field_theory, condensed_matter…
├── memory/        ← Obsidian vault integration
└── config/        ← YAML runtime configuration
```

## Non-Negotiable Rules

- Never use `|| true` on lint or test commands — failures must block CI.
- Never invent error codes inline — use codes from `docs/contracts/error-codes.md`.
- Never accept a function parameter that has zero code paths reading it.
- Never use bare `except:` — always catch a specific exception type.
- Run `yamllint . && ruff check . --ignore E501 && python tools/validate_registry.py` before
  every commit.

## Branch Convention

Branch pattern: `claude/<description>-<SESSION_ID>`
Current dev branch: `claude/briefcase-phase-implementation-gK4j5`

# FORGE Project Vision

> Derived from FORGE_MASTER_INDEX.md and v0.1-spec.md. Last updated: 2026-03-18.

## Mission

FORGE is a production engineering AI for Reid Industries / Quantanium.
It performs complete engineering task cycles: task intake → specialist analysis →
FEA/simulation tooling → verification → vault persistence → structured output.

Every number must have units. Every claim must be falsifiable.
No data enters the vault without passing the verification gate stack.

## Active Milestone

**v0.1 MVP** — Single-discipline structural analysis, Aladdin-3B motor mount bracket,
end-to-end traced and persisted.

Critical path:

```
Task Intake → Blackboard Init → ME Specialist → GMSH (mesh) → CalculiX (FEA)
→ Verification Stack → Vault Persistence → Output Report
```

## Repository Structure

- `forge-core/` — C++ core runtime (blackboard, router, orchestrator, logger)
- `forge_agent/` — Python runtime (agents, MCP wrappers, memory, core)
- `forge-agents/` — Agent definitions (SKILL.md, prompts, agent cards)
- `forge-tests/` — Test fixtures (YAML)
- `forge-vault/` — Obsidian vault
- `briefcase/` — Tauri/TypeScript desktop UI (Void Vanguard)

## Frozen Interfaces

All v1 contracts are frozen:
- Blackboard Schema v1 (`docs/contracts/blackboard-schema.md`)
- Agent Output Contract v1 (`docs/contracts/agent-output-contract.md`)
- MCP Wrapper Envelope v1 (`docs/contracts/mcp-wrapper-envelope.md`)
- Vault Frontmatter Schema v1 (`docs/contracts/vault-frontmatter-schema.md`)
- Trace ID Standard v1 (`docs/contracts/trace-id-standard.md`)
- Error Codes v1 (`docs/contracts/error-codes.md`)

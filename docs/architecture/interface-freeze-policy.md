# Interface Freeze Policy

> How interfaces are frozen and what it takes to change them.

---

## What "Frozen" Means

A frozen interface means:
1. The schema/contract is finalized and published
2. All producers and consumers are built against it
3. Changes require a new ADR + version bump + migration plan
4. Breaking changes are not allowed without major version bump

---

## Frozen Interfaces (v1)

| Interface | Document | Version | Frozen Since |
|---|---|---|---|
| Blackboard Schema | `docs/contracts/blackboard-schema.md` | v1 | 2026-03-05 |
| Agent Output Contract | `docs/contracts/agent-output-contract.md` | v1 | 2026-03-05 |
| MCP Wrapper Envelope | `docs/contracts/mcp-wrapper-envelope.md` | v1 | 2026-03-05 |
| Vault Frontmatter Schema | `docs/contracts/vault-frontmatter-schema.md` | v1 | 2026-03-05 |
| Trace ID Standard | `docs/contracts/trace-id-standard.md` | v1 | 2026-03-05 |
| Error Codes | `docs/contracts/error-codes.md` | v1 | 2026-03-05 |

---

## Change Process

1. Identify the need for change
2. Write an ADR (see `docs/planning/governance/decision-log-template.md`)
3. Determine if the change is additive (minor version) or breaking (major version)
4. If breaking: identify all consumers and write migration plan
5. ADR approved → schema updated → version bumped → consumers updated
6. Old version supported for one milestone after deprecation

---

## Schema Versioning Policy

See `docs/contracts/schema-versioning-policy.md` for version numbering rules.

Short form:
- `v1`, `v2`, ... for major (breaking) changes
- `v1.1`, `v1.2`, ... for minor (additive) changes
- Patch versions not used for schemas (schemas are either compatible or not)

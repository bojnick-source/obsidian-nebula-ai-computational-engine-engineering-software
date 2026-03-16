---
type: index
status: active
vault_version: "1.0"
obsidian_min_version: "1.12"
created: 2026-03-16
---

# FORGE Engineering Knowledge Vault

> Open this folder in **Obsidian ≥ v1.12** to navigate the knowledge graph.
> Minimum required community plugins: **Dataview**, **Templater**, **obsidian-git**.

---

## Quick Nav

| Section | Purpose |
|---|---|
| [[indexes/node-index\|Node Index]] | All vault notes (auto-generated) |
| [[indexes/gap-index\|Gap Index]] | Open engineering gaps |
| [[indexes/contradiction-index\|Contradiction Index]] | Flagged contradictions |
| [[indexes/stale-index\|Stale Index]] | Notes due for review |
| `inbox/` | Unprocessed inputs (NotebookLM exports, raw research) |
| `notebooks/` | NotebookLM source notebooks (PDFs, links, exports) |

---

## Vault Rules

1. **Never write unverified data** — all notes must pass the verification stack before landing here.
2. **Never delete notes** — flag `status: stale` or `status: disputed`, never delete.
3. **Amnesia check is mandatory** — every write is followed by a read-back confirmation.
4. **All writes are git commits** — obsidian-git plugin auto-commits on save.
5. **Frontmatter is required** — every note must conform to `forge-memory/schemas/vault_frontmatter.schema.yaml`.

---

## NotebookLM Workflow

Research material (PDFs, papers, specs) enters the vault via **NotebookLM** before being
processed by the Librarian agent:

```
External source
  → NotebookLM (notebooks/) — summarise, extract key claims
  → inbox/ — exported markdown + frontmatter stub
  → Librarian agent — validate, verify, write to engineering/ or mathematics/
  → forge-vault (verified note)
```

See [[forge-memory/obsidian/notebooklm|NotebookLM Integration Spec]] for full workflow.

---

## Obsidian Version

Tested with **Obsidian v1.12.4** (released 2026-02-27).
Community plugins pinned in `.obsidian/community-plugins.json`.

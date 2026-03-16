# NotebookLM Integration Spec

> **What:** Google NotebookLM is used as the *pre-ingestion* layer before external research
> material enters the FORGE vault. It processes PDFs, papers, and web sources into structured
> summaries that the Librarian agent then validates and writes as verified vault notes.

---

## Role in the Memory Pipeline

```
External sources (PDFs, papers, specs, datasheets)
        │
        ▼
  ┌─────────────┐
  │  NotebookLM │  — forge-vault/notebooks/<project>/<source>.pdf
  │  (Google)   │  — Audio Overview (podcast) for rapid domain intake
  └─────┬───────┘
        │  exports: summary + key claims + citations
        ▼
  forge-vault/inbox/<slug>.md   ← frontmatter stub, unverified
        │
        ▼
  Librarian agent (forge_agent)
        │  validates claims against existing vault
        │  passes through verification stack
        ▼
  forge-vault/engineering/ or mathematics/  ← verified note
```

---

## notebooks/ Directory Convention

Store source material uploaded to NotebookLM here:

```
forge-vault/notebooks/
  aladdin-3b/
    al7075_datasheet.pdf
    fea_convergence_study.pdf
  project-vanguard/
    ...
  research/
    isa_1976_standard_atmosphere.pdf
    ...
```

**Rule:** PDFs committed to `notebooks/` are the source-of-truth for any vault note
that carries `source_type: notebooklm_export`. Do not delete a PDF while any vault
note references it.

---

## inbox/ Convention

NotebookLM exports land in `forge-vault/inbox/` as markdown with a minimal frontmatter
stub. The Librarian agent processes inbox notes on the next pipeline run.

### Required frontmatter stub for inbox notes

```yaml
---
type: finding          # or: derivation | decision | gap
status: inbox          # sentinel — Librarian will update this
source_type: notebooklm_export
source_notebook: notebooks/aladdin-3b/al7075_datasheet.pdf
confidence: null       # set by Librarian after verification
agent: null            # set by Librarian
created: 2026-03-16
---
```

### Inbox processing rules

1. Librarian scans `inbox/` on every pipeline start.
2. For each inbox note: extract claims → cross-check vault → assign confidence.
3. On pass: move to correct `engineering/` or `mathematics/` path, update frontmatter.
4. On fail: create a `gap/` note with `status: unresolved`, log to `indexes/gap-index.md`.
5. Original inbox file is deleted only after the verified note exists and amnesia-checked.

---

## Audio Overview Usage

NotebookLM can generate a podcast-style audio overview of a notebook. Use this for:
- Rapid onboarding to a new engineering domain before assigning a specialist agent
- Pre-brief before a full pipeline run on a new project

Audio files are **not** committed to the vault (large binary). Reference the notebook
source in the vault note instead.

---

## Hard Rules

1. **NotebookLM summaries are not verified data.** They must pass the full Librarian +
   Verifier stack before landing in `engineering/` or `mathematics/`.
2. **inbox/ is never the final destination.** Notes stuck in inbox for > 7 days
   are automatically flagged as gaps.
3. **Source PDFs are committed.** If a claim cites a PDF, that PDF must exist in
   `notebooks/` at the referenced path.
4. **No hallucinated citations.** The Verifier must be able to resolve every citation
   to a file in `notebooks/` or an external URI stored in frontmatter.

---

## Agent Handoff

| Step | Agent | Input | Output |
|---|---|---|---|
| Ingest | Librarian | `inbox/*.md` | Verified note or gap note |
| Verify claims | Verifier | Draft note + source PDF | `status: validated` or `status: disputed` |
| Contradiction check | Librarian | New note + vault index | Contradiction entry if conflict |
| Final write | Librarian | Validated note | `engineering/` or `mathematics/` note |

---

## See Also

- [Obsidian Manager Spec](obsidian_manager.md)
- [Intake Operation](intake.md)
- [Gap Detection](gap_detection.md)
- `forge-vault/notebooks/` — source PDFs
- `forge-vault/inbox/` — unprocessed NotebookLM exports

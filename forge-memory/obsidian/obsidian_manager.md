# Obsidian Manager — Behavior Spec

> Master specification for all memory system operations.

---

## Responsibilities

The Obsidian Manager (implemented in the Librarian agent + any supporting C++ vault I/O layer) is responsible for:

1. **Intake** — Validating and writing new notes to the vault
2. **Retrieval** — Routing queries and returning ranked context
3. **Gap Detection** — Creating gap notes for unresolved questions
4. **Strengthening** — Updating evidence and confidence on existing notes
5. **Contradiction Handling** — Detecting and managing conflicting claims
6. **Synthesis** — Generating higher-order synthesis notes from clusters
7. **Decay Detection** — Flagging stale notes for review
8. **Agent Thinking Catalog** — Persisting reasoning records

---

## Pre-Ingestion Layer

External research material enters the vault via **NotebookLM** before the Librarian agent
processes it. See [NotebookLM Integration Spec](notebooklm.md) for the full workflow.

```
External source → NotebookLM (notebooks/) → inbox/ → Librarian → vault
```

---

## Operation Contracts

Each operation is specified in its own file:
- [NotebookLM Pre-Ingestion](notebooklm.md)
- [Intake](intake.md)
- [Retrieval / Routing](routing.md)
- [Gap Detection](gap_detection.md)
- [Strengthening](strengthening.md)
- [Contradiction Handler](contradiction_handler.md)
- [Synthesis](synthesis.md)
- [Decay Detection](decay_detection.md)
- [Pathway Strength](pathway_strength.md)

---

## Hard Rules

1. **No unverified writes.** Only verified outputs (passed all required gates) may be written to the vault.
2. **No auto-delete.** Notes are never automatically deleted. They are flagged for review.
3. **Amnesia check is mandatory.** Every write is followed by a read to confirm persistence.
4. **Contradictions create disputed notes.** Never overwrite — version the old note and create a disputed note.
5. **All writes are git commits** (when git_auto_commit is true in config).

---

## Vault Directory Structure

```
forge-vault/
  engineering/
    constraints/
    derivations/
    design-decisions/
    failure-modes/
    materials/
    research/
    manufacturing/
    adversarial-logs/
    empirical-crosschecks/
    agent-thinking/
  mathematics/
    formulations/
    solvers/
  ilc/
    links/
    clusters/
    synthesis-proposals/
  projects/
    aladdin-3b/
    project-vanguard/
    phoenix/
  indexes/
  backups/
```

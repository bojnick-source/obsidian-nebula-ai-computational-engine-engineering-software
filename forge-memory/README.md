# forge-memory

Memory system for FORGE: Obsidian vault integration, schemas, routing, synthesis logic.

## Structure

```
schemas/                        # Frontmatter and note type schemas (YAML Schema)
  vault_frontmatter.schema.yaml
  note_types.yaml
  blackboard_entry.schema.yaml
  agent_thinking.schema.yaml
  ilc_link.schema.yaml
  schema_versions.yaml
obsidian/                       # Behavior specs for memory operations
  obsidian_manager.md           # Master spec
  intake.md
  gap_detection.md
  routing.md
  synthesis.md
  strengthening.md
  contradiction_handler.md
  decay_detection.md
  pathway_strength.md
templates/                      # Note templates for each note type
  finding.md
  derivation.md
  decision.md
  gap.md
  synthesis.md
  agent-thinking.md
  ilc-link.md
tests/                          # Phase-based memory tests
```

## Key Invariant

The vault is a hard dependency. If vault writes fail, the pipeline halts.
If vault reads fail, pipeline continues with empty context + gap flags.
Amnesia check is mandatory after every write.

See `docs/architecture/memory-neural-model.md` for the conceptual model.

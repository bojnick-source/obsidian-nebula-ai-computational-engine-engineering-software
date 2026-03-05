# forge-vault

The FORGE engineering knowledge vault. All verified engineering findings, derivations, decisions, gaps, and agent reasoning records are stored here as Obsidian-compatible markdown notes with structured YAML frontmatter.

## Structure

```
engineering/
  constraints/          # Engineering constraints by domain
  derivations/          # Mathematical derivations
  design-decisions/     # Design decisions with rationale
  failure-modes/        # Known failure modes
  materials/            # Material property findings
  research/             # Research notes and references
  manufacturing/        # Manufacturing constraints and findings
  adversarial-logs/     # Logs from antagonist debate (V1)
  empirical-crosschecks/ # Empirical validation against known results
  agent-thinking/       # Agent reasoning records

mathematics/
  formulations/         # Mathematical formulations used in analysis
  solvers/              # Solver configuration notes

ilc/
  links/               # Inter-domain link candidates (V1)
  clusters/            # ILC clusters
  synthesis-proposals/ # Proposed synthesis notes from ILC clusters

projects/
  aladdin-3b/          # Aladdin-3B project knowledge
  project-vanguard/    # Vanguard project knowledge
  phoenix/             # Phoenix project knowledge

indexes/
  node-index.md        # Index of all vault nodes
  gap-index.md         # Index of all open gaps
  contradiction-index.md # Index of all contradictions
  stale-index.md       # Index of stale/review-flagged notes

backups/
  snapshots/           # Snapshot archives
  restore-tests/       # Restore drill logs
```

## Rules

1. Never write unverified data here — all notes must pass the verification stack
2. Never delete notes — flag for review only
3. Every write must pass the amnesia check
4. All notes must have valid frontmatter per `forge-memory/schemas/vault_frontmatter.schema.yaml`
5. Git auto-commit is on by default

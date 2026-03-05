# Planning Priority Map

> P0/P1/P2 tagging of every planning document and scaffold item.

---

## P0 — Must be complete before first build

### Root Documents
- [x] README.md
- [x] FORGE_MASTER_INDEX.md
- [x] FORGE_CATALOG.md (v8+)
- [x] ROADMAP.md
- [x] RISK_REGISTER.md
- [x] DECISIONS.md
- [x] CHANGELOG.md
- [x] CMakeLists.txt (placeholder)
- [x] pyproject.toml (placeholder)
- [x] .gitignore
- [x] .editorconfig

### Architecture Docs
- [x] docs/architecture/system-overview.md
- [x] docs/architecture/core-loop.md
- [x] docs/architecture/agent-topology.md
- [x] docs/architecture/memory-neural-model.md
- [x] docs/architecture/verifier-architecture.md
- [x] docs/architecture/degraded-modes.md
- [x] docs/architecture/mcp-a2a-boundaries.md
- [x] docs/architecture/observability-standard.md
- [x] docs/architecture/interface-freeze-policy.md
- [x] docs/architecture/tactical-switches.md

### Contracts
- [x] docs/contracts/blackboard-schema.md
- [x] docs/contracts/agent-output-contract.md
- [x] docs/contracts/mcp-wrapper-envelope.md
- [x] docs/contracts/vault-frontmatter-schema.md
- [x] docs/contracts/trace-id-standard.md
- [x] docs/contracts/error-codes.md
- [x] docs/contracts/schema-versioning-policy.md

### MVP Planning
- [x] docs/planning/mvp/v0.1-spec.md
- [x] docs/planning/mvp/v0.1-acceptance-test.md
- [x] docs/planning/mvp/v0.1a-fallback-spec.md
- [x] docs/planning/mvp/mvp-cut-line.md

### Risk + Decisions
- [x] docs/planning/risk/risk-register.md
- [x] RISK_REGISTER.md (summary)
- [x] DECISIONS.md

### Fixture Structure (P0 — structure must exist, content can be P1)
- [x] forge-tests/fixtures/phase_1_1/ (structure)
- [x] forge-tests/fixtures/v0_1_acceptance/ (structure)
- [x] forge-tests/fixtures/verifier_red_team/ (structure)

---

## P1 — Can be finalized during build

- docs/planning/catalog/ (historical versions)
- docs/planning/governance/
- docs/ops/ (all ops docs)
- docs/toolchain/
- docs/projects/ (project-specific docs)
- forge-agents/prompts/ (prompt content)
- forge-memory/obsidian/ (behavior specs content)
- forge-tools/mcp-wrappers/ (wrapper specs content)
- forge-verification/red-team/ (fixture cases)
- forge-ops/ (telemetry, security, cost, backup)
- Aladdin-3B project docs

---

## P2 — Future planning (V1 / R&D)

- docs/research/
- All R&D toolchain docs
- Phoenix / Vanguard full specs
- RTSA scaffold docs
- NVIDIA physics stack docs
- External ecosystem full bridge specs

# FORGE Changelog

All notable changes to FORGE are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- Full planning scaffold (monorepo structure, all directories and planning documents)
- FORGE Master Index (1-page planning index)
- Tiered roadmap (MVP / V1 / R&D)
- Risk register (10 top risks with triggers and mitigations)
- Decision log (10 frozen ADRs)
- Architecture docs: system overview, core loop, agent topology, memory model, verifier architecture, degraded modes, observability standard
- Contract docs: blackboard schema, agent output contract, MCP wrapper envelope, vault frontmatter schema, trace ID standard, error codes, schema versioning policy
- MVP spec (v0.1), acceptance test, fallback spec, cut line
- Planning docs: catalog v6/v7/v8/current, tiered roadmap, milestone gates, risk register/heatmap
- Ops docs: provider failover, security model, CI/CD pipeline, cost tracking, backup/recovery, incident response
- forge-core header scaffold (all .hpp files for all subsystems)
- forge-agents registry and prompt scaffolds
- forge-memory schema and obsidian behavior specs
- forge-tools MCP wrapper specs for all MVP and V1 tools
- forge-verification specs and red-team fixtures
- forge-tests fixture structure
- forge-vault knowledge structure
- external-ecosystem import scaffold
- .github/workflows: CI, security, nightly fixtures, vault integrity
- CMakeLists.txt placeholder
- pyproject.toml placeholder

---

## [0.0.1] — 2026-03-05

### Added
- Initial repository creation
- README stub

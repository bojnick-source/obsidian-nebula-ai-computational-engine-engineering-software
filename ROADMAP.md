# FORGE Roadmap

> Tiered roadmap: MVP → V1 → R&D.

## MVP (v0.1)

- [x] CLI entry point (`forge --version`, `--smoke-test`)
- [x] Config loader (forge.yaml)
- [x] JSONL structured logging
- [x] Blackboard inter-agent store
- [x] Model router with provider fallback
- [x] 7 agent definitions (ORCH-01, E-01, E-05, V-STRUCT, V-ADV, LIB-01, TEST-01)
- [x] 23 unit tests

## V1 (planned)

- [ ] C++ core runtime (forge-core)
- [ ] A2A agent transport (gRPC + local shim)
- [ ] MCP tool wrappers (CalculiX, GMSH, FreeTO)
- [ ] Full Obsidian neural memory integration
- [ ] Structural & adversarial verification pipeline
- [ ] Project pipelines (Aladdin-3B / Vanguard / Phoenix)

## R&D

- [ ] RTSA — Runtime Topological Self-Assembly
- [ ] ILC — Inter-Lattice Connectivity agent synthesis
- [ ] NVIDIA physics stack integration

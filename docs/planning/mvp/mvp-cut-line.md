# MVP Cut Line

> Everything below this line is EXCLUDED from v0.1. Adding anything here to v0.1 scope requires a new ADR.

---

## Excluded from v0.1

### Agent System
- Antagonist agents (any domain)
- A2A debate lifecycle
- Arbitration
- ILC link detection
- Emergent agent synthesis
- Prompt Engineer agent (prompt registry, A/B tests)

### Memory System
- Contradiction detection and handling
- ILC link generation
- Memory synthesis proposals
- Decay detection / stale index
- Agent thinking catalog

### Verification
- Contradiction Gate
- Assumption Gate (hidden assumption scan)
- Adversarial Falsification
- Confidence Calibration

### Tools
- OpenFOAM (CFD)
- SU2 (CFD)
- XFOIL (2D aero)
- FreeTO (topology optimization)
- Swan (topology optimization)
- beso (topology optimization)
- OpenLSTO (topology optimization)
- OCCT (geometry kernel)
- PicoGK (volumetric geometry)
- OpenVSP (aircraft geometry)
- JSBSim (flight dynamics)
- Gazebo Harmonic
- Isaac Sim
- NVIDIA PhysX / Warp / Newton / PhysicsNeMo
- preCICE (multi-physics coupling)
- FEniCSx (advanced FEA)
- Video intelligence
- Empirical crosscheck layer

### Infrastructure
- Provider failover / circuit breaker
- HashiCorp Vault secrets (use env vars at MVP)
- Cost tracking events
- Per-call cost logging
- Budget threshold alerts
- Full observability dashboard

### External Ecosystem
- CATIA import
- Solid Edge import
- Fusion360 engineering import
- Blender import
- X-Plane simulator bridge
- Geometry import validation gate (full)

### Projects
- Project Vanguard pipeline
- Phoenix Nigredo Dracenix pipeline

### R&D
- RTSA (runtime topological self-assembly)
- O3DE digital twin
- Anything in `docs/research/`

---

## What IS in v0.1

See `docs/planning/mvp/v0.1-spec.md`.

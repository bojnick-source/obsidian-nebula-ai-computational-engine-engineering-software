# Canonical Toolchain Reference

> Single source of truth for all tools in the FORGE toolchain.
> Tool IDs here must match `forge-tools/tool-registry/canonical_toolchain_ids.yaml`.

---

## MVP Toolchain (v0.1)

| Tool | ID | Purpose | License | Wrapper |
|---|---|---|---|---|
| GMSH | `gmsh` | Mesh generation | GPL-2.0 | `forge-tools/mcp-wrappers/gmsh/` |
| CalculiX | `calculix` | Linear static FEA | GPL-2.0 | `forge-tools/mcp-wrappers/calculix/` |

---

## V1 Toolchain

| Tool | ID | Purpose | License | Language | Wrapper |
|---|---|---|---|---|---|
| FreeTO | `freeto` | Topology optimization | MIT | MATLAB | Planned |
| beso | `beso` | Topology optimization (fallback) | open-source | Python | Planned |
| OpenFOAM | `openfoam` | CFD solver | GPL-3.0 | Python (foamlib) | Planned |
| SU2 | `su2` | CFD solver | LGPL-2.1 | Python | Planned |
| XFOIL | `xfoil` | 2D airfoil analysis | open-source | Python | Planned |
| OCCT | `occt` | Geometry kernel | LGPL-2.1 | Python | Planned |
| PicoGK | `picogk` | Volumetric geometry | Apache-2.0 | C# (LEAP 71) | Planned |
| OpenVSP | `openvsp` | Aircraft geometry | NASA-1.3 | Python | Planned |
| JSBSim | `jsbsim` | Flight dynamics | LGPL-2.1 | Python | Planned |

---

## R&D Toolchain

| Tool | ID | Purpose | License | Language | Status |
|---|---|---|---|---|---|
| preCICE | `precice` | Multi-physics coupling | LGPL-3.0 | Python/C++ | Evaluating |
| FEniCSx | `fenics` | Advanced FEA | LGPL-3.0 | Python (API) | Evaluating |
| Swan | `swan` | Topology optimization | Academic | MATLAB | License pending |
| OpenLSTO | `openlsto` | Topology optimization | open-source | MATLAB/C++ | Evaluating |
| Gazebo Harmonic | `gazebo` | Robot simulation | Apache-2.0 | Python/C++ | Evaluating |
| Isaac Sim | `isaac_sim` | Robot simulation | NVIDIA | GPU/Python | Evaluating |
| PhysX | `physx` | Physics | NVIDIA | GPU/C++ | Evaluating |
| Warp | `warp` | Differentiable GPU physics | NVIDIA | GPU/Python (JIT) | Evaluating |
| Newton | `newton` | Robotics physics | NVIDIA | GPU/C++ | Evaluating |
| PhysicsNeMo | `physicsnemo` | Physics-ML | NVIDIA | GPU/Python | Evaluating |

> Language column references [Polyglot Architecture Doctrine](../architecture/polyglot-doctrine.md).
> Tools marked GPU/\* do not enter production until `forge-gpu/` wrapper architecture is approved.

---

## External Ecosystem (not MCP wrappers — import channels)

| Tool | Purpose | Import Channel |
|---|---|---|
| CATIA V5/V6 | Engineering CAD | `external-ecosystem/cad-imports/catia/` |
| Solid Edge | Engineering CAD | `external-ecosystem/cad-imports/solid-edge/` |
| Fusion360 | Engineering/Concept CAD | `external-ecosystem/cad-imports/fusion360/` |
| Blender | Visual/Concept | `external-ecosystem/cad-imports/blender/` |
| X-Plane | Flight simulation | `external-ecosystem/simulator-bridges/xplane/` |

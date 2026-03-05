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

| Tool | ID | Purpose | License | Wrapper |
|---|---|---|---|---|
| FreeTO | `freeto` | Topology optimization | MIT | Planned |
| beso | `beso` | Topology optimization (fallback) | open-source | Planned |
| OpenFOAM | `openfoam` | CFD solver | GPL-3.0 | Planned |
| SU2 | `su2` | CFD solver | LGPL-2.1 | Planned |
| XFOIL | `xfoil` | 2D airfoil analysis | open-source | Planned |
| OCCT | `occt` | Geometry kernel | LGPL-2.1 | Planned |
| PicoGK | `picogk` | Volumetric geometry | Apache-2.0 | Planned |
| OpenVSP | `openvsp` | Aircraft geometry | NASA-1.3 | Planned |
| JSBSim | `jsbsim` | Flight dynamics | LGPL-2.1 | Planned |

---

## R&D Toolchain

| Tool | ID | Purpose | License | Status |
|---|---|---|---|---|
| preCICE | `precice` | Multi-physics coupling | LGPL-3.0 | Evaluating |
| FEniCSx | `fenics` | Advanced FEA | LGPL-3.0 | Evaluating |
| Swan | `swan` | Topology optimization | Academic | License pending |
| OpenLSTO | `openlsto` | Topology optimization | open-source | Evaluating |
| Gazebo Harmonic | `gazebo` | Robot simulation | Apache-2.0 | Evaluating |
| Isaac Sim | `isaac_sim` | Robot simulation | NVIDIA | Evaluating |
| PhysX | `physx` | Physics | NVIDIA | Evaluating |
| Warp | `warp` | GPU physics | NVIDIA | Evaluating |
| Newton | `newton` | Physics | NVIDIA | Evaluating |
| PhysicsNeMo | `physicsnemo` | Physics-ML | NVIDIA | Evaluating |

---

## External Ecosystem (not MCP wrappers — import channels)

| Tool | Purpose | Import Channel |
|---|---|---|
| CATIA V5/V6 | Engineering CAD | `external-ecosystem/cad-imports/catia/` |
| Solid Edge | Engineering CAD | `external-ecosystem/cad-imports/solid-edge/` |
| Fusion360 | Engineering/Concept CAD | `external-ecosystem/cad-imports/fusion360/` |
| Blender | Visual/Concept | `external-ecosystem/cad-imports/blender/` |
| X-Plane | Flight simulation | `external-ecosystem/simulator-bridges/xplane/` |

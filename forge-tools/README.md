# forge-tools

MCP (Model Context Protocol) wrappers for all external tools in the FORGE toolchain.

## MVP Tools (required for v0.1)

| Tool | Purpose | Wrapper Status |
|---|---|---|
| GMSH | Mesh generation | Spec written |
| CalculiX | FEA solver (linear static) | Spec written |

## V1 Tools

| Tool | Purpose | Wrapper Status |
|---|---|---|
| FreeTO | Topology optimization | Spec pending |
| OpenFOAM | CFD | Spec pending |
| SU2 | CFD | Spec pending |
| XFOIL | 2D airfoil analysis | Spec pending |
| OCCT | Geometry kernel | Spec pending |
| PicoGK | Volumetric geometry | Spec pending |
| OpenVSP | Aircraft geometry | Spec pending |
| JSBSim | Flight dynamics | Spec pending |
| preCICE | Multi-physics coupling | Spec pending |

## Structure

```
mcp-wrappers/<tool>/
  README.md           # Overview and usage
  WRAPPER_SPEC.md     # Behavior contract
  INPUT_SCHEMA.md     # Typed input contract
  OUTPUT_SCHEMA.md    # Typed output contract
  ERRORS.md           # Error codes and handling
  FIXTURES.md         # Test fixtures and golden outputs

tool-registry/
  canonical_toolchain_ids.yaml   # Single source of truth for tool IDs
  wrapper_status.yaml            # Status of each wrapper
  degraded_modes.yaml            # Stub/degraded configs per tool

docs/
  wrapper-envelope-contract.md   # → docs/contracts/mcp-wrapper-envelope.md
  subprocess-sandbox-policy.md
  tool-timeout-policy.md
```

## Adding a New Wrapper

1. Create directory in `mcp-wrappers/<tool-id>/`
2. Write WRAPPER_SPEC.md, INPUT_SCHEMA.md, OUTPUT_SCHEMA.md, ERRORS.md
3. Add to `tool-registry/canonical_toolchain_ids.yaml`
4. Add to `tool-registry/wrapper_status.yaml`
5. Define degraded mode stub in `tool-registry/degraded_modes.yaml`
6. Add fixtures in FIXTURES.md
7. Register in `forge-core/configs/skill_server_map.yaml`

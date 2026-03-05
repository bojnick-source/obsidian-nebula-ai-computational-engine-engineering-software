# GMSH MCP Wrapper Spec

**Tool ID:** `gmsh`
**Wrapper Version:** `1.0.0`
**MVP Status:** Required

---

## Purpose

Invokes GMSH (open-source mesh generator) to create finite element meshes from geometry specifications. Accepts parametric geometry or geometry files. Returns mesh files (.msh) validated for FEA use.

---

## Invocation Model

1. Accept geometry input (parametric Python GMSH API script or .brep/.step file)
2. Run GMSH via Python API (subprocess or in-process)
3. Validate mesh quality (non-zero elements, no degenerate elements, manifold)
4. Return mesh file path and quality metrics

---

## Input

See `INPUT_SCHEMA.md`.

Key fields:
- `geometry_type`: `parametric_python` | `brep` | `step` (MVP: parametric_python only)
- `geometry_spec`: python script string (for parametric) or file path
- `mesh_algorithm`: `Delaunay` | `Frontal` (default: Delaunay)
- `element_order`: 1 | 2 (default: 1, linear elements)
- `max_element_size_mm`: float

---

## Output

See `OUTPUT_SCHEMA.md`.

Key fields:
- `mesh_path`: path to .msh file
- `element_count`: integer
- `node_count`: integer
- `quality_min_jacobian`: float (should be > 0)
- `degenerate_element_count`: integer (must be 0)

---

## Validation (mandatory before output)

1. element_count > 0
2. degenerate_element_count == 0
3. quality_min_jacobian > 0.0 (all elements valid)
4. Mesh is manifold (no hanging nodes or disconnected regions)

If any validation fails: return error, do not pass mesh to CalculiX.

---

## Degraded Mode

If GMSH fails >2 times: activate `DEGRADED_MESH` mode, halt solver phase.

---

## Timeout Policy

Default: 30s. Larger geometries may require up to 120s (configure per task).

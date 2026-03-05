# CalculiX MCP Wrapper Spec

**Tool ID:** `calculix`
**Wrapper Version:** `1.0.0`
**MVP Status:** Required

---

## Purpose

Invokes CalculiX (open-source FEA solver) to perform linear static structural analysis. Accepts a mesh file (GMSH .msh output) and boundary/load conditions. Returns stress fields, displacements, and reaction forces.

---

## Invocation Model

1. Write input files to a sandboxed temp directory
2. Invoke `ccx` subprocess with input deck
3. Parse `.frd` output file for results
4. Extract: max von Mises stress, max displacement, reaction forces at constraints
5. Clean up temp directory
6. Return result envelope

---

## Input

See `INPUT_SCHEMA.md`.

Key fields:
- `mesh_path`: path to .msh file from GMSH wrapper
- `material`: material properties (E, nu, density)
- `boundary_conditions`: list of constrained nodes/faces
- `loads`: list of applied loads (force, pressure)
- `analysis_type`: `linear_static` (only type at MVP)

---

## Output

See `OUTPUT_SCHEMA.md`.

Key fields:
- `max_von_mises_mpa`: float (MPa)
- `max_displacement_mm`: float (mm)
- `safety_factor`: float (if yield strength provided)
- `result_file_path`: path to .frd output (for audit)
- `stdout_hash`: sha256 of ccx stdout

---

## Degraded Mode

If CalculiX fails >2 times: return stub output with:
- All numeric results set to -1.0
- `degraded: true` flag
- `gap_flags`: ["FEA result requires live solver verification"]

---

## Timeout Policy

Default: 60s per analysis. Configurable. See `docs/tool-timeout-policy.md`.

---

## Sandbox Policy

CalculiX runs in a subprocess sandbox with:
- Max CPU: 60s
- Max memory: 512MB
- No network access
- Read-only access to mesh input file
- Write access to temp output directory only

See `docs/subprocess-sandbox-policy.md`.

---

## Error Codes

See `ERRORS.md`.

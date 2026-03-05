# CalculiX Input Schema v1

```yaml
$schema: "forge/mcp/calculix/input/v1"

# Required
mesh_path: string              # Path to GMSH .msh file
analysis_type: string          # "linear_static" (MVP only)
material:
  name: string                 # e.g., "6061-T6"
  E_gpa: float                 # Young's modulus in GPa
  nu: float                    # Poisson's ratio (dimensionless)
  density_kg_m3: float         # Density in kg/m³
  yield_strength_mpa: float    # Yield strength in MPa (optional but recommended)

boundary_conditions:
  - type: string               # "fixed" | "pinned" | "roller"
    target: string             # "node_set:<name>" | "face_set:<name>"

loads:
  - type: string               # "force" | "pressure"
    target: string             # "node_set:<name>" | "face_set:<name>"
    magnitude: float           # N for force, MPa for pressure
    direction: [float, float, float]  # unit vector [x, y, z]

# Optional
safety_factor_limit: float     # If provided, SF computed against yield
trace_id: string               # Propagated from MCP envelope
```

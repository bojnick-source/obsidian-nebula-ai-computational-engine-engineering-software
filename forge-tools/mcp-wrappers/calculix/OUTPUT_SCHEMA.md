# CalculiX Output Schema v1

```yaml
$schema: "forge/mcp/calculix/output/v1"

# Always present
status: string               # "success" | "error" | "timeout" | "degraded"
trace_id: string
duration_ms: integer

# Present on success
max_von_mises_mpa: float     # Maximum von Mises stress in MPa
max_displacement_mm: float   # Maximum nodal displacement in mm
reaction_forces:
  - node_set: string
    fx_n: float              # Force in N
    fy_n: float
    fz_n: float
safety_factor: float         # yield_strength / max_von_mises (if yield provided)

# Optional: location of max values
max_stress_location:
  element_id: integer
  node_id: integer
  coordinates: [float, float, float]  # mm

# Audit
result_file_path: string     # Path to .frd output file
stdout_hash: string          # sha256
exit_code: integer

# Degraded mode
degraded: boolean            # true if stub result
gap_flags: list[string]      # populated in degraded mode
```

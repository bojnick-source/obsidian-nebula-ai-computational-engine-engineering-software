# CalculiX Wrapper Error Codes

| Code | Trigger | Recovery |
|---|---|---|
| `ERR_TOOL_SUBPROCESS_FAIL` | `ccx` exits non-zero | Retry (max 3); activate degraded after 3 |
| `ERR_TOOL_TIMEOUT` | ccx exceeds timeout_ms | Retry with extended timeout; activate degraded |
| `ERR_TOOL_OUTPUT_INVALID` | .frd file missing or unparseable | Log and return error; do not return partial |
| `ERR_TOOL_SANDBOX_VIOLATION` | CPU/memory limit exceeded | Return error; do not retry without limit increase |
| `WARN_TOOL_DEGRADED` | Stub result returned | Flag in output; add gap_flags |

## Common ccx Failure Causes

1. **Mesh quality issues**: Non-manifold mesh, degenerate elements → validate mesh before invoking CalculiX
2. **Singular stiffness matrix**: Under-constrained model → check boundary conditions
3. **Material property errors**: Negative E or nu out of range → validate input schema before invoke
4. **Convergence failure**: Not applicable to linear static, but log if detected

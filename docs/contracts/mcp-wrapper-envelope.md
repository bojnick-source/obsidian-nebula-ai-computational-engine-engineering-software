# MCP Wrapper Envelope Contract v1

> **STATUS: FROZEN**
> All MCP tool wrappers must accept inputs and produce outputs in this envelope format.

---

## Request Envelope

```yaml
$schema: "forge/mcp/request/v1"
tool_id: string (required)           # e.g., "calculix", "gmsh"
wrapper_version: string (semver)     # e.g., "1.0.0"
trace_id: string (uuid-v4, required)
task_id: string (required)
invocation_id: string (uuid-v4)      # unique per invocation (for retries)
timestamp: string (ISO8601)
timeout_ms: integer (required)
input: object                        # tool-specific; defined per tool WRAPPER_SPEC.md
sandbox:
  enabled: boolean (default: true)
  max_memory_mb: integer
  max_cpu_seconds: integer
```

---

## Response Envelope

```yaml
$schema: "forge/mcp/response/v1"
tool_id: string (required)
wrapper_version: string (semver)
trace_id: string (required)          # echoed from request
invocation_id: string (required)     # echoed from request
timestamp: string (ISO8601)
duration_ms: integer
status: enum [success, error, timeout, degraded]
error_code: string (nullable)        # from docs/contracts/error-codes.md
error_detail: string (nullable)
output: object                       # tool-specific; defined per tool OUTPUT_SCHEMA.md
metadata:
  stdout_hash: string (sha256)       # hash of subprocess stdout for auditability
  stderr_lines: integer              # number of stderr lines (not content)
  exit_code: integer
```

---

## Error Handling Rules

1. Network/subprocess errors → `status: error`, `error_code: ERR_TOOL_SUBPROCESS_FAIL`
2. Timeout → `status: timeout`, `error_code: ERR_TOOL_TIMEOUT`
3. Output schema validation failure → `status: error`, `error_code: ERR_TOOL_OUTPUT_INVALID`
4. Degraded mode stub → `status: degraded`, `error_code: null`, output contains placeholder values with flags

---

## Retry Policy

- Maximum 4 total attempts per request (1 initial attempt + up to 3 retries)
- Exponential backoff between retries: 1s, 2s, 4s
- New `invocation_id` for each attempt
- If all attempts fail, activate degraded mode on the final attempt

---

## Sandbox Policy

See `forge-tools/docs/subprocess-sandbox-policy.md`.

---

## Version History

| Version | Changes |
|---|---|
| v1 | Initial frozen envelope |

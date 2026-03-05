# Subprocess Sandbox Policy

> All MCP tool wrappers that invoke subprocesses must comply with this policy.

---

## Required Sandbox Constraints

| Constraint | Default | Configurable? |
|---|---|---|
| Max CPU time | 60s | Yes, per tool |
| Max memory | 512 MB | Yes, per tool |
| Network access | Disabled | No |
| Filesystem access | Temp dir only (RW) + input files (RO) | No |
| Process creation | None beyond the tool subprocess | No |

---

## Implementation

At MVP: use Python `subprocess` with `ulimit` or `resource` module to enforce CPU and memory limits. Network isolation via not passing any network credentials.

V1: evaluate container-based sandboxing (e.g., gVisor, seccomp) for stronger isolation.

---

## Failure on Sandbox Violation

If a subprocess violates sandbox limits:
- Kill the subprocess immediately
- Return `error_code: ERR_TOOL_SANDBOX_VIOLATION`
- Do not return partial results
- Log with trace_id

---

## Audit Trail

All subprocess invocations log:
- `stdout_hash` (sha256 of captured stdout)
- `stderr_lines` (count only, not content — to avoid log injection)
- `exit_code`
- `duration_ms`

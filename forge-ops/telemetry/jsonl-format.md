# JSONL Log Format

> Every log line emitted by FORGE follows this format. See `docs/architecture/observability-standard.md` for the full observability standard.

---

## Log Line Schema

```json
{
  "ts": "2026-03-05T10:23:45.123Z",
  "level": "INFO",
  "trace_id": "a3f1b2c4-8e9d-4f0a-b123-456789abcdef",
  "task_id": "t-8b2c3d4e-...",
  "component": "orchestrator",
  "phase": "specialist",
  "event": "specialist_dispatch_start",
  "agent_id": "me_specialist",
  "tool_id": null,
  "invocation_id": null,
  "error_code": null,
  "payload": {
    "domain": "mechanical_engineering",
    "component": "motor_mount_bracket"
  }
}
```

---

## Required Fields (all lines)

| Field | Type | Description |
|---|---|---|
| `ts` | string (ISO8601) | Timestamp with milliseconds |
| `level` | string | INFO \| WARN \| ERROR \| DEBUG |
| `trace_id` | string (UUID v4) | Task trace ID |
| `component` | string | Emitting component |
| `event` | string | Event name |

## Conditional Fields

| Field | Required when |
|---|---|
| `task_id` | Always (if task context available) |
| `phase` | Inside core loop |
| `agent_id` | Agent-related events |
| `tool_id` | Tool invocation events |
| `invocation_id` | Tool invocation events |
| `error_code` | Error/warning events |
| `payload` | Additional context |

---

## Phase Start/End Events (mandatory)

```json
{"event": "phase_start", "phase": "specialist", ...}
{"event": "phase_end",   "phase": "specialist", "duration_ms": 2340, "status": "success", ...}
```

---

## Event Name Conventions

- Phase lifecycle: `phase_start`, `phase_end`
- Agent: `agent_dispatch_start`, `agent_response_received`
- Tool: `tool_invocation_start`, `tool_invocation_complete`, `tool_invocation_failed`
- Verification: `gate_pass`, `gate_fail`, `gate_warn`
- Vault: `vault_write_start`, `vault_write_success`, `vault_write_failed`, `amnesia_check_pass`, `amnesia_check_fail`
- Degraded: `degraded_mode_activated`, `tactical_switch_activated`, `degraded_mode_deactivated`
- Escalation: `escalation_triggered`

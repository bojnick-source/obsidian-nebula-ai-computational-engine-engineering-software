# Observability Standard

> How FORGE is instrumented. What must be logged. What must be traceable.

---

## Required Log Fields (every log line)

```json
{
  "ts": "ISO8601 timestamp",
  "level": "INFO | WARN | ERROR | DEBUG",
  "trace_id": "uuid-v4",
  "component": "orchestrator | specialist | verifier | librarian | mcp_wrapper | router",
  "event": "event_name",
  "error_code": "ERR_xxx | null",
  "payload": {}
}
```

See `forge-core/include/forge/logging/jsonl_logger.hpp` and `docs/contracts/error-codes.md`.

---

## Trace ID Propagation

- Assigned at task intake (Phase 0)
- Carried through all phases of the core loop
- Attached to: blackboard entries, agent outputs, tool invocations, vault notes, log lines
- Never regenerated mid-loop (trace ID is immutable per task)

---

## Metrics Catalog

| Metric | Type | Description |
|---|---|---|
| `forge.task.duration_ms` | Histogram | End-to-end task duration |
| `forge.phase.duration_ms` | Histogram | Per-phase duration (labels: phase name) |
| `forge.verification.gate_result` | Counter | Pass/fail per gate (labels: gate name) |
| `forge.tool.invocation_duration_ms` | Histogram | Tool invocation time (labels: tool name) |
| `forge.tool.error_count` | Counter | Tool errors (labels: tool name, error code) |
| `forge.vault.write_duration_ms` | Histogram | Vault write time |
| `forge.vault.amnesia_check_result` | Counter | Pass/fail amnesia check |
| `forge.provider.health_status` | Gauge | Provider availability (labels: provider name) |
| `forge.cost.tokens_used` | Counter | Tokens per agent call (labels: agent, provider) |
| `forge.degraded_mode.active` | Gauge | Which degraded modes are active |

---

## Diagnosability Gates

Every phase must emit at minimum:
1. Phase start event with trace_id
2. Phase end event with duration and success/fail
3. Error events with error_code on any failure

Phases missing these events fail the diagnosability gate in CI.

---

## Dashboard Spec

See `forge-ops/telemetry/dashboard-spec.md`.

Key views:
1. Task throughput and latency
2. Verification gate pass rates by gate
3. Tool reliability (error rates by tool)
4. Provider health and failover events
5. Vault write/read reliability
6. Cost per task by provider

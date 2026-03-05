# Blackboard Schema v1

> **STATUS: FROZEN**
> Changes require ADR + major version bump.

---

## Purpose

The blackboard is the shared in-memory state for a single FORGE task execution. All agents, tools, and verifiers read from and write to the blackboard using typed entries.

---

## Schema (v1)

```yaml
# blackboard_entry.schema.yaml — v1
$schema: "forge/blackboard/v1"
trace_id: string (uuid-v4, required)
created_at: string (ISO8601, required)
updated_at: string (ISO8601, required)

task:
  id: string (required)
  type: enum [engineering_full, engineering_lite, non_engineering]
  classification_confidence: float (0.0–1.0)
  input_text: string (required)
  component_context: string (optional)
  project: string (optional)  # e.g., "aladdin-3b"

decomposition:
  constraints: list[string]
  load_cases: list[string]
  assumptions: list[string]
  gap_flags: list[string]
  domains_required: list[string]

specialist_outputs:
  - agent_id: string
    version: string (semver)
    domain: string
    result: object (per agent-output-contract.md)
    trace_id: string
    timestamp: string (ISO8601)

tool_results:
  - tool_id: string
    wrapper_version: string
    input_ref: string  # hash or reference to input artifact
    output: object (per mcp-wrapper-envelope.md)
    trace_id: string
    timestamp: string (ISO8601)

verification_results:
  - gate: enum [contract, unit, dimensional, provenance, contradiction, assumption, adversarial, confidence]
    result: enum [pass, fail, warn]
    error_code: string (nullable)
    detail: string (nullable)
    timestamp: string (ISO8601)

vault_artifacts:
  - note_id: string
    note_type: string
    vault_path: string
    trace_id: string
    amnesia_check: enum [pass, fail, not_run]

final_output:
  result_summary: string
  unresolved_gaps: list[string]
  what_would_falsify: list[string]
  confidence: float (0.0–1.0)
  artifact_refs: list[string]
  status: enum [complete, partial, failed, degraded]
```

---

## Concurrency Rules

- Multiple agents may read concurrently
- Writes to distinct fields may proceed concurrently
- Writes to the same field use optimistic locking (version counter per field)
- See `forge-core/include/forge/blackboard/concurrency_guard.hpp`

---

## Version History

| Version | Changes |
|---|---|
| v1 | Initial frozen schema |

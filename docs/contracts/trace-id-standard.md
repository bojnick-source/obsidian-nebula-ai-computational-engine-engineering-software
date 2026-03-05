# Trace ID Standard v1

> **STATUS: FROZEN**

---

## Format

Trace IDs are UUID v4 strings: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`

Example: `a3f1b2c4-8e9d-4f0a-b123-456789abcdef`

---

## Assignment Rules

1. **One trace ID per task** — assigned at Phase 0 (intake), immutable for the task lifecycle
2. **Never regenerated** mid-loop — if a retry occurs, the same trace ID carries through
3. **Sub-invocations** (tool calls, agent calls within a task) carry the parent task's trace ID
4. **Batch tasks** — each sub-task in a batch gets its own trace ID; parent batch gets a batch ID

---

## Propagation Requirements

Trace ID must be present in:
- Every blackboard entry (`trace_id` field)
- Every agent output packet (`trace_id` field)
- Every MCP tool invocation request/response envelope (`trace_id` field)
- Every vault note frontmatter (`trace_id` field)
- Every JSONL log line (`trace_id` field)
- Every verification result (`trace_id` field, inherited from input)

---

## Lookup

Given a trace_id, you must be able to retrieve:
1. The original task (blackboard)
2. All agent outputs produced for the task
3. All tool invocations
4. All verification results
5. All vault notes created
6. All log lines

This is the diagnosability guarantee. If any of the above is unresolvable from trace_id, it is a logging bug.

---

## Generation

`forge-core/include/forge/common/ids.hpp` provides `TraceId::generate()`.

Python equivalent: `uuid.uuid4()` from stdlib.

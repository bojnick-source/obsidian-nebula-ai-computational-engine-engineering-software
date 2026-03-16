---
id: {{uuid}}
type: agent-thinking
domain: {{domain}}
created_at: {{iso8601}}
updated_at: {{iso8601}}
trace_id: {{trace_id}}
agent_id: {{agent_id}}
agent_version: {{agent_version}}
confidence: 1.0
pathway_strength: 0.1
op_sequence: {{op_sequence}}
triggered_by: {{triggered_by}}
what: {{what}}
why: {{why}}
how: {{how}}
outcome: {{outcome}}
duration_ms: {{duration_ms}}
tags: []
---

# Journal: {{what}}

| Field | Value |
|---|---|
| **Outcome** | {{outcome}} |
| **When** | `{{iso8601}}` |
| **Duration** | `{{duration_ms}} ms` |
| **Sequence** | `#{{op_sequence}}` in trace `{{trace_id_short}}…` |
| **Causality** | {{causality}} |

---

## WHAT

> {{what}}

## WHY

> {{why}}

## HOW

> {{how}}

## State Before

{{state_before}}

## State After

{{state_after}}

## Annotations

{{notes}}

# FORGE Core Loop

> The canonical description of a single FORGE task execution cycle.

---

## Loop Phases

```
Phase 0: Input Intake
  ├── Task received (engineering / non-engineering / lite / full)
  ├── Trace ID assigned (globally unique, propagated to all artifacts)
  ├── Task classification
  └── Blackboard initialized

Phase 1: Skill Routing
  ├── Model router consults routing config
  ├── Provider health checked
  ├── Target workflow selected (full / degraded / lite)
  └── Fallback chain determined

Phase 2: System Decomposition
  ├── Constraints extracted
  ├── Load cases enumerated
  ├── Assumptions listed
  ├── Gap flags initialized
  └── Blackboard fields populated (schema v1)

Phase 3: Memory Pre-Flight
  ├── Vault routing (core or degraded)
  ├── Relevant notes retrieved (context package)
  ├── Gap candidates fetched
  └── ILC candidates loaded (V1)

Phase 4: Specialist Phase
  ├── Specialist dispatched (domain-matched)
  ├── Agent output contract validated
  ├── Blackboard updated with specialist outputs
  └── Gap flags updated

Phase 5: Antagonist Phase  [V1 / full mode only]
  ├── Antagonist paired with specialist
  ├── A2A debate initiated
  ├── Objections registered
  ├── Arbitration if unresolved
  └── Adversarial log written

Phase 6: Tool Execution Phase
  ├── MCP wrapper invoked (GMSH → CalculiX at MVP)
  ├── Solver output parsed
  ├── Result envelope validated
  └── Blackboard ingested with solver results

Phase 7: Verification Phase
  ├── Contract gate
  ├── Unit gate
  ├── Dimensional gate
  ├── Provenance gate
  ├── Contradiction gate  [V1]
  ├── Assumption gate  [V1]
  ├── Adversarial falsification  [V1]
  └── Confidence calibration  [V1]

Phase 8: Persistence Phase
  ├── Vault note created/updated
  ├── Agent thinking record written
  ├── Adversarial logs written  [V1]
  └── Retrieval sanity check (amnesia check)

Phase 9: Output Phase
  ├── Final engineering result assembled
  ├── Traceable artifact references attached
  ├── Unresolved gaps listed
  └── what_would_falsify field populated
```

---

## Loop Guards

| Guard | Limit | Action on breach |
|---|---|---|
| Max loop iterations | 5 | Escalate to human; write partial result with gap flags |
| Max tool retries | 3 | Activate degraded mode; flag result |
| Verification failure | Any mandatory gate | Reject output; do not write to vault |
| Vault write failure | After 2 retries | Halt pipeline; escalate |

---

## Degraded Mode Activations

See `docs/architecture/degraded-modes.md` for the full table.

Short summary: if provider is unavailable, stub-mode activates. If vault is unavailable, pipeline halts (vault is a hard dependency).

---

## Trace ID Propagation

Every artifact generated in the loop carries the task's trace ID:
- Blackboard entry: `trace_id`
- Agent output: `trace_id`
- Tool invocation: `trace_id`
- Vault note frontmatter: `trace_id`
- JSONL log lines: `trace_id`

See `docs/contracts/trace-id-standard.md`.

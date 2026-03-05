# Agent Output Contract v1

> **STATUS: FROZEN**
> All specialist, antagonist, verifier, and librarian agents must produce outputs conforming to this contract.

---

## Required Fields (all agents)

```yaml
agent_id: string (required)          # e.g., "me_specialist"
agent_version: string (semver)       # e.g., "1.0.0"
trace_id: string (uuid-v4, required)
task_id: string (required)
timestamp: string (ISO8601, required)
domain: string (required)            # e.g., "mechanical_engineering"
output_type: enum [analysis, critique, verification, memory_op, synthesis]
```

---

## Content Fields (type-dependent)

### For `output_type: analysis` (specialists)

```yaml
findings:
  - claim: string (required)
    value: number | string (required)
    units: string (required for numeric)
    confidence: float (0.0–1.0, required)
    provenance:
      source: string (required)
      specificity: enum [high, medium, low]
      citation: string (required)  # author/standard/section
    assumptions:
      - string  # explicit list; empty list is acceptable, null is not
    what_would_falsify:
      - string
gaps_identified:
  - string
recommendations:
  - string
```

### For `output_type: critique` (antagonists — V1)

```yaml
objections:
  - claim_ref: string (reference to specialist claim being challenged)
    objection: string
    severity: enum [fatal, major, minor]
    alternative: string (optional)
resolved: boolean
arbitration_required: boolean
```

### For `output_type: verification` (verifiers)

```yaml
gate: enum [contract, unit, dimensional, provenance, contradiction, assumption, adversarial, confidence]
result: enum [pass, fail, warn]
error_code: string (nullable)
detail: string
```

### For `output_type: memory_op` (librarian)

```yaml
operation: enum [intake, retrieve, strengthen, gap_create, contradiction_flag, synthesis_propose]
note_ids_affected: list[string]
amnesia_check_result: enum [pass, fail, not_run]
```

---

## Validation

All outputs validated against this contract at:
1. Agent output emission (agent-side validation)
2. Contract gate in verification stack (receiver-side validation)

---

## Version History

| Version | Changes |
|---|---|
| v1 | Initial frozen contract |

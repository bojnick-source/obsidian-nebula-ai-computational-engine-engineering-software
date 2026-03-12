# Vault Frontmatter Schema v1

> **STATUS: FROZEN**
> All notes written to the forge-vault must have frontmatter conforming to this schema.

---

## Schema (v1)

```yaml
---
# Required fields — every note
id: string              # UUID v4, assigned at creation
type: enum              # finding | derivation | decision | gap | synthesis | agent-thinking | ilc-link
domain: string          # mechanical_engineering | materials | electrical_engineering | plasma |
                        # magnetics | control_systems | thermal_fluids | acoustics | safety_se |
                        # biomedical | mathematics | cross_domain
created_at: string      # ISO8601
updated_at: string      # ISO8601
trace_id: string        # task trace ID that created this note
agent_id: string        # agent that created this note
agent_version: string   # semver
confidence: float       # 0.0–1.0
pathway_strength: float # 0.0–1.0 (starts at 0.1, incremented on access)

# Required for type: finding | derivation | synthesis
provenance:
  source: string        # author/standard/section
  specificity: enum     # high | medium | low
  citation: string      # full citation string
  last_verified: string # ISO8601

# Required for type: finding
units: string           # SI units of primary result (if numeric)

# Optional — all types
project: string         # aladdin-3b | project-vanguard | phoenix | cross_project
component: string       # specific component reference
tags: list[string]
related_notes: list[string]   # IDs of related notes (wiki-links)
gap_flags: list[string]       # unresolved gaps identified in this note
assumptions: list[string]     # explicit assumptions for this finding
what_would_falsify: list[string]

# Contradiction handling
superseded_by: string   # ID of note that supersedes this one (if any)
disputes: list[string]  # IDs of notes this contradicts
dispute_status: enum    # open | resolved | escalated

# Decay / stale detection
last_accessed: string   # ISO8601
access_count: integer
review_flagged: boolean
---
```

---

## Note Type Rules

| Type | Required Additional Fields |
|---|---|
| `finding` | `provenance`, `units` (if numeric), `confidence` |
| `derivation` | `provenance`, step-by-step content |
| `decision` | `rationale`, `alternatives_considered` (in content) |
| `gap` | `gap_description`, `gap_flags` |
| `synthesis` | `provenance`, `source_note_ids` (in content) |
| `agent-thinking` | `agent_id`, `task_id`, reasoning content |
| `ilc-link` | `source_domain`, `target_domain`, `link_type` |

---

## Version History

| Version | Changes |
|---|---|
| v1 | Initial frozen schema |

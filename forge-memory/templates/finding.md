---
id: {{uuid}}
type: finding
domain: {{domain}}
created_at: {{iso8601}}
updated_at: {{iso8601}}
trace_id: {{trace_id}}
agent_id: {{agent_id}}
agent_version: {{agent_version}}
confidence: {{confidence}}
pathway_strength: 0.1
project: {{project}}
component: {{component}}
units: {{units}}
provenance:
  source: {{source}}
  specificity: {{high|medium|low}}
  citation: {{citation}}
  last_verified: {{iso8601}}
assumptions:
  - {{assumption_1}}
what_would_falsify:
  - {{falsification_1}}
gap_flags: []
tags: []
related_notes: []
access_count: 0
review_flagged: false
---

# {{title}}

## Finding

{{finding_description}}

## Value

**Result:** {{value}} {{units}}

## Analysis Context

{{analysis_context}}

## Evidence

{{evidence_description}}

## Assumptions

See frontmatter `assumptions` field.

## Limitations

{{limitations}}

## What Would Falsify This Finding

See frontmatter `what_would_falsify` field.

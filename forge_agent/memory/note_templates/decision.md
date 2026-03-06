---
type: decision
title: "{{title}}"
date: "{{date}}"
problem_id: "{{problem_id}}"
decision_maker: "{{agent}}"
status: "{{status}}"
tags: [decision, engineering]
---

# {{title}}

## Context
{{context}}

## Decision
**Chosen approach:** {{chosen_approach}}

## Alternatives Considered
{% for alt in alternatives %}
### {{alt.name}}
- **Pros:** {{alt.pros}}
- **Cons:** {{alt.cons}}
- **Rejected because:** {{alt.rejection_reason}}
{% endfor %}

## Rationale
{{rationale}}

## Consequences
- **Positive:** {{positive_consequences}}
- **Negative / Trade-offs:** {{negative_consequences}}
- **Risks:** {{risks}}

## Standards Compliance
{% for standard in standards %}
- {{standard}}
{% endfor %}

## Validation Required
{{validation_required}}

---
type: derivation
title: "{{title}}"
date: "{{date}}"
problem_id: "{{problem_id}}"
agent: "{{agent}}"
tags: [derivation, engineering]
---

# {{title}}

## Problem Statement
{{problem_statement}}

## Assumptions
{% for assumption in assumptions %}
- {{assumption}}
{% endfor %}

## Governing Equations
{% for eq in governing_equations %}
$${{eq}}$$
{% endfor %}

## Derivation Steps
{% for step in derivation_steps %}
### Step {{loop.index}}: {{step.description}}
{{step.detail}}
{% if step.equation %}
$${{step.equation}}$$
{% endif %}
{% endfor %}

## Result
$${{result_equation}}$$

**Numerical value:** {{numerical_result}} {{unit}}

## Sanity Checks
{% for check in sanity_checks %}
- **{{check.type}}:** {{check.detail}} ✓
{% endfor %}

## References
{% for ref in references %}
- {{ref}}
{% endfor %}

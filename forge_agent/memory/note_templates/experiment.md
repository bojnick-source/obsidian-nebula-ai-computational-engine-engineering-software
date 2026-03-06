---
type: experiment
title: "{{title}}"
date: "{{date}}"
problem_id: "{{problem_id}}"
agent: "{{agent}}"
tool: "{{tool}}"
status: "{{status}}"
tags: [experiment, simulation]
---

# {{title}}

## Hypothesis
{{hypothesis}}

## Setup
- **Tool / Solver:** {{tool}}
- **Model:** {{model_description}}
- **Boundary Conditions:** {{boundary_conditions}}
- **Material:** {{material}}
- **Mesh:** {{mesh_description}}

## Parameters
| Parameter | Value | Unit |
|-----------|-------|------|
{% for p in parameters %}
| {{p.name}} | {{p.value}} | {{p.unit}} |
{% endfor %}

## Results
| Quantity | Value | Unit | Notes |
|----------|-------|------|-------|
{% for r in results %}
| {{r.quantity}} | {{r.value}} | {{r.unit}} | {{r.notes}} |
{% endfor %}

## Convergence
- **Residuals:** {{residuals}}
- **Mesh sensitivity:** {{mesh_sensitivity}}
- **GCI:** {{gci}}

## Observations
{{observations}}

## Conclusions
{{conclusions}}

## Follow-up
{{follow_up}}

---
type: failure_mode
title: "{{title}}"
date: "{{date}}"
problem_id: "{{problem_id}}"
severity: "{{severity}}"
probability: "{{probability}}"
rpn: "{{rpn}}"
tags: [failure-mode, fmea, safety]
---

# {{title}}

## Failure Mode Description
{{description}}

## Affected Component
**Component:** {{component}}
**Function:** {{function}}

## Failure Cause(s)
{% for cause in causes %}
- {{cause}}
{% endfor %}

## Failure Effect(s)
### Local Effect
{{local_effect}}

### System Effect
{{system_effect}}

### End Effect
{{end_effect}}

## Detection Method
{{detection_method}}

## Severity / Probability / Detection Ratings
| Parameter | Rating | Justification |
|-----------|--------|---------------|
| Severity (S) | {{severity_rating}}/10 | {{severity_justification}} |
| Probability (O) | {{occurrence_rating}}/10 | {{occurrence_justification}} |
| Detection (D) | {{detection_rating}}/10 | {{detection_justification}} |
| **RPN** | **{{rpn}}** | S × O × D |

## Recommended Actions
{% for action in recommended_actions %}
- **{{action.type}}:** {{action.description}} (responsible: {{action.owner}})
{% endfor %}

## Status
{{status}}

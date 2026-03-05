# Agent Leveling Policy

> How agents are promoted from planned → implemented → validated → production.

---

## Agent Status Levels

| Status | Meaning |
|---|---|
| `planned` | Card defined, no prompt yet |
| `mvp` | Prompt v1 written, prompt tests defined, ready for MVP build |
| `v1` | Targeted for V1 milestone |
| `rd` | R&D / future consideration |
| `deprecated` | No longer active |

---

## Promotion Gates

### planned → mvp
- [ ] Agent card written and reviewed
- [ ] Prompt v1.0.0 written
- [ ] Prompt tests written (≥3 expected-behavior assertions)
- [ ] Output contract fields verified against agent-output-contract.md
- [ ] ADR written if new agent type

### mvp → implemented
- [ ] Agent callable via A2A local shim
- [ ] Prompt tests pass against a real LLM call
- [ ] Contract gate passes on agent output

### implemented → validated
- [ ] Integration test in forge-tests/ passes
- [ ] Red-team fixtures show correct rejection behavior
- [ ] No hallucinated provenance in test outputs

---

## Prompt Versioning

Prompts follow semantic versioning:
- `v1.0.0` — initial production prompt
- `v1.1.0` — additive improvement (new instruction, clarification)
- `v2.0.0` — breaking change (output format change, scope change)

All versions kept in `prompts/<id>/` directory.
Each version has a corresponding CHANGELOG.md entry.

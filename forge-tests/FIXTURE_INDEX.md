# forge-tests — Fixture Index

All test fixtures used across FORGE. This file is the single source of truth for
what is tested where. Update this whenever adding new fixtures or directories.

---

## Fixture Directories

| Directory | Component Under Test | Milestone | Description |
|---|---|---|---|
| `fixtures/phase_1_1/` | Blackboard typed write | Lane B (Core Runtime) | Validates `blackboard.add_entry()` accepts typed fields and rejects schema violations |
| `fixtures/verifier_red_team/` | VerifierAgent gate | Lane F (Verification) | Known-bad inputs that the verifier MUST catch — used for regression + red-team testing |
| `fixtures/v0_1_acceptance/` | Full v0.1 pipeline | MVP v0.1 | End-to-end acceptance scenarios: intake → specialist → tool → verify → vault |

---

## Fixture Files

| File | Tags | Input Summary | Expected Outcome |
|---|---|---|---|
| `fixtures/phase_1_1/blackboard_typed_write.yaml` | blackboard, typing, schema | Typed blackboard entry (task_id, agent, fields) | Entry written with correct schema; malformed entries rejected |
| `fixtures/verifier_red_team/provenance_errors.yaml` | verifier, provenance, red-team | Specialist output with fabricated/missing citations | `overall_verdict: disputed`; provenance errors flagged |
| `fixtures/verifier_red_team/unit_errors.yaml` | verifier, units, red-team | Specialist output with SI unit violations | `overall_verdict: disputed`; unit_errors populated |
| `fixtures/v0_1_acceptance/motor_mount_bracket.yaml` | e2e, aladdin-3b, acceptance | Aladdin-3B motor mount bracket structural problem | Verified FEA result with confidence ≥ 0.8, vault note written |

---

## Planned Fixtures (not yet populated)

| Directory | Component | Milestone |
|---|---|---|
| `fixtures/phase_1_2/` | Memory intake (vault write + read-back) | Lane C (Memory Core) |
| `fixtures/phase_1_3/` | Gap detection (missing knowledge detection) | Lane C |
| `fixtures/phase_1_4/` | Routing (skill → agent → MCP) | Lane B/D |
| `fixtures/phase_1_6/` | Thinking catalog (agent-thinking note format) | Lane C |
| `fixtures/geometry_import/` | CAD geometry validation gates | Lane E (Tool Wrappers) |
| `fixtures/provider_failover/` | LLM provider failover + degraded mode | Lane B |
| `golden/v0_1_acceptance/` | Golden outputs for acceptance tests | MVP v0.1 |
| `golden/verifier_red_team/` | Expected verifier verdicts for red-team inputs | Lane F |
| `golden/routing/` | Expected routing decisions for known problem types | Lane B |
| `integration/happy_path/` | Full pipeline happy path (no failures) | MVP v0.1 |
| `integration/degraded_mode_paths/` | Pipeline with tool unavailability | Lane E/H |
| `integration/tactical_switch_paths/` | Runtime config switch scenarios | Lane B |

---

## How to Add a Fixture

1. Create a `.yaml` file under the appropriate `fixtures/` subdirectory.
2. Use this schema:
   ```yaml
   description: "What this fixture tests"
   tags: [component, scenario]
   milestone: "v0.1 | Lane X"
   input:
     # ... problem input
   expected:
     # ... expected output / verdict
   ```
3. Add a row to the table above.
4. Reference the fixture in the relevant pytest file (e.g., `tests/test_regressions.py`).

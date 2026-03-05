# forge-tests

Test fixtures, golden outputs, integration tests, and red-team packs for FORGE.

## Structure

```
fixtures/
  phase_1_1/          # Blackboard typed write fixtures
  phase_1_2/          # Memory intake fixtures
  phase_1_3/          # Gap detection fixtures
  phase_1_4/          # Routing fixtures
  phase_1_6/          # Thinking catalog fixtures
  verifier_red_team/  # Known-bad inputs that must be rejected
  geometry_import/    # Geometry validation test cases
  provider_failover/  # Provider failure simulation fixtures
  v0_1_acceptance/    # v0.1 acceptance test inputs and expectations

golden/
  v0_1_acceptance/    # Expected outputs for acceptance test
  verifier_red_team/  # Expected rejections
  routing/            # Expected routing decisions
  contradiction/      # Expected contradiction detection outcomes

integration/
  happy_path/         # End-to-end happy path tests
  degraded_mode_paths/
  tactical_switch_paths/
  failover_paths/

reports/
  catch-rate/         # Verifier catch rate reports
  regression/         # Regression test reports
  fixture-coverage/   # Fixture coverage reports
```

## Running Tests

```bash
# All tests (when implemented)
pytest forge-tests/ -v

# Acceptance test only
pytest forge-tests/fixtures/v0_1_acceptance/ -v

# Red-team only
pytest forge-tests/fixtures/verifier_red_team/ -v

# With degraded mode
pytest forge-tests/integration/degraded_mode_paths/ -v
```

## Fixture Format

Each fixture is a YAML file with:
- `input`: the test input
- `expected`: expected output or behavior
- `tags`: [unit | integration | red_team | acceptance]
- `milestone`: [mvp | v1 | rd]

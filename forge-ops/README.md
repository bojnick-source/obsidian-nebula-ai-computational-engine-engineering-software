# forge-ops

Operations, telemetry, security, cost tracking, backup, and incident response for FORGE.

## Structure

```
telemetry/
  jsonl-format.md         # JSONL log line format spec
  metrics-catalog.md      # All metrics definitions
  trace-propagation.md    # How trace IDs propagate
  dashboard-spec.md       # Dashboard views

security/
  hashicorp-vault-paths.md    # HCV secret paths (V1)
  approle-permissions.md      # AppRole permission model
  secret-rotation-policy.md   # Rotation schedule and procedure
  precommit-secrets-scan.md   # Git pre-commit secret scanning

cost/
  event-schema.md         # Cost event log format
  budget-thresholds.md    # Alert thresholds
  reporting.md            # Cost reporting and rollup

backup/
  vault-backup-policy.md  # Vault backup schedule and retention
  restore-procedures.md   # How to restore from backup
  integrity-checks.md     # How to verify backup integrity

incident/
  provider-outage-playbook.md       # LLM provider outage response
  vault-corruption-playbook.md      # Vault corruption response
  degraded-mode-escalation.md       # Escalation path for degraded modes
```

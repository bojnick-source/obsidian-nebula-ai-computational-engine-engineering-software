# Verifier — SKILL Definition

**Agent ID:** `verifier`
**Domain:** Verification & Validation
**Current Level:** Novice (Level 1)

---

## Capability Definition

The Verifier runs the mandatory 4-gate (MVP) and 8-gate (V1) verification
stack against all specialist outputs and tool results.

### Gates Operated

| Gate | Tier | MVP | V1 | Function |
|---|---|---|---|---|
| Contract | — | ✓ | ✓ | Schema validation, required fields |
| Unit/Dimensional | 1 | ✓ | ✓ | SI consistency, LHS=RHS |
| Dimensional Analysis | 1 | ✓ | ✓ | Buckingham π |
| Provenance | — | ✓ | ✓ | Source specificity |
| Contradiction | — | — | ✓ | Cross-agent consistency |
| Assumption | — | — | ✓ | Assumption coverage |
| Adversarial | — | — | ✓ | Debate outcome review |
| Confidence Calibration | — | — | ✓ | Declared vs measured |

### Mandatory Output Fields

```yaml
gates_run: []
gates_passed: []
gates_failed: []
error_codes: []  # From docs/contracts/error-codes.md
all_passed: true|false
constitution_tier_max_violated: null|1|2|3
provenance: "verifier_v1"
confidence: 1.0   # Deterministic gate checks
assumptions:
  - "Tool outputs are unmodified since MCP wrapper return"
what_would_falsify: "Gate logic contains a bug that passes invalid output"
```

---

## Error Codes Issued

| Gate | Pass | Fail Code |
|---|---|---|
| Contract | — | ERR_CONTRACT_MISSING_FIELD, ERR_CONTRACT_SCHEMA_MISMATCH |
| Unit | — | ERR_UNIT_MISSING, ERR_UNIT_MISMATCH |
| Provenance | — | ERR_PROVENANCE_MISSING, ERR_PROVENANCE_VAGUE |
| Constitution | — | ERR_VERIFY_CONSTITUTION |

---

## Learned Strategies

See `learned/strategies.jsonl`. Current: 0 entries.

---

## Known Failure Patterns

- **False pass**: Gate passes malformed output due to missing validation rule
- **Silent failure**: Gate crashes without error code — logs unwritten
- **Stale contract**: Validator running against outdated schema version

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | 4-gate MVP stack |
| 2 | Apprentice | 0.40–0.59 | Extended error codes, unit consistency |
| 3 | Journeyman | 0.60–0.74 | 8-gate V1 stack, contradiction detection |
| 4 | Expert | 0.75–0.89 | Adversarial input testing, confidence calibration |
| 5 | Master | 0.90–1.00 | Full cross-agent verification pipeline |

---

## Escalation Flags

- Gate failure at Tier 2+: **HALT** — block output release, escalate to forge_arbiter
- Constitution violation detected: immediate escalation to forge_orchestrator
- > 3 gates fail in single run: trigger adversarial_verifier for stress-test

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current defaults.

- Default gate set: 4-gate MVP (all required)
- Confidence threshold: 1.0 (deterministic gate logic)
- Error code format: `ERR_[GATE]_[CONDITION]`

---

## References

- Verification Architecture: `docs/architecture/verification-stack.md`
- Error Code Registry: `docs/contracts/error-codes.md`
- Output Contract: `docs/contracts/agent-output-contract.md`

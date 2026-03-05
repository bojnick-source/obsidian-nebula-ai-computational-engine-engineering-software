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

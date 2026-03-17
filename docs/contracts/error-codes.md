# Error Codes v1

> **STATUS: FROZEN**
> All error codes used by FORGE components. New codes require a minor version bump to this document.

---

## Code Taxonomy

| Prefix | Domain |
|---|---|
| `ERR_CONTRACT_*` | Data contract violations |
| `ERR_UNIT_*` | Unit/dimensional errors |
| `ERR_PROVENANCE_*` | Provenance/citation errors |
| `ERR_TOOL_*` | MCP tool invocation errors |
| `ERR_VAULT_*` | Memory/vault errors |
| `ERR_PROVIDER_*` | LLM provider errors |
| `ERR_VERIFY_*` | Verification stack errors |
| `ERR_SYSTEM_*` | Internal system errors |
| `ERR_TOOL_ASSEMBLY_*` | Assembly / DFA tool errors |
| `ERR_CONSTITUTION_*` | Engineering constitution rule violations |
| `WARN_*` | Warnings (non-fatal; logged but don't halt pipeline) |

---

## Contract Errors

| Code | Description |
|---|---|
| `ERR_CONTRACT_VIOLATION` | Required field missing or wrong type |
| `ERR_CONTRACT_VERSION_MISSING` | Schema version field absent |
| `ERR_CONTRACT_VERSION_INCOMPATIBLE` | Schema version not supported |

---

## Unit / Dimensional Errors

| Code | Description |
|---|---|
| `ERR_UNIT_MISSING` | Numeric result has no units |
| `ERR_UNIT_INCONSISTENT` | Mixed units in same expression |
| `ERR_UNIT_NORMALIZATION_FAIL` | Cannot normalize to SI |
| `ERR_DIMENSIONAL_MISMATCH` | LHS ≠ RHS dimensions in equation |
| `ERR_DIMENSIONAL_INCOMPATIBLE` | Result units incompatible with declared output type |

---

## Provenance Errors

| Code | Description |
|---|---|
| `ERR_PROVENANCE_MISSING` | No source attribution |
| `ERR_PROVENANCE_UNSPECIFIC` | Source too vague (e.g., "textbook") |
| `ERR_PROVENANCE_UNPARSEABLE` | Citation string cannot be parsed |
| `WARN_PROVENANCE_UNVERIFIED` | Source not independently verified |

---

## Tool Errors

| Code | Description |
|---|---|
| `ERR_TOOL_SUBPROCESS_FAIL` | Tool subprocess exited with error |
| `ERR_TOOL_TIMEOUT` | Tool exceeded timeout |
| `ERR_TOOL_OUTPUT_INVALID` | Tool output failed schema validation |
| `ERR_TOOL_SANDBOX_VIOLATION` | Tool exceeded sandbox resource limits |
| `WARN_TOOL_DEGRADED` | Tool running in stub/degraded mode |

---

## Tool Assembly Errors

Emitted by `assembly_specialist` / `dfa_dfm_specialist` agents (see `docs/architecture/assembly-dfa.md`).

| Code | Description |
|---|---|
| `ERR_TOOL_ASSEMBLY_INTERFERENCE` | Mesh intersection volume > 0 — parts overlap |
| `ERR_TOOL_ASSEMBLY_TOOL_BLOCKED` | No assembly tool reaches the fastener from any approach angle |
| `ERR_TOOL_ASSEMBLY_CYCLE` | Assembly DAG contains a directed cycle — sequence unsolvable |
| `ERR_TOOL_ASSEMBLY_UNPLACED` | One or more components have no valid placement in assembly order |
| `ERR_TOOL_ASSEMBLY_MASS_OVERRUN` | Assembly mass exceeds declared budget |
| `WARN_TOOL_ASSEMBLY_CLEARANCE` | Clearance between components below minimum (< 0.5 mm) |
| `WARN_TOOL_ASSEMBLY_BLIND` | Fastener inaccessible for in-service inspection |
| `WARN_TOOL_ASSEMBLY_SERVICEABILITY` | Serviceability score below threshold — maintenance time penalised |

---

## Constitution / Engineering Contract Errors

Emitted when outputs violate the Engineering Constitution tier rules (see `docs/architecture/v3/engineering-constitution.md`).

| Code | Description |
|---|---|
| `ERR_CONSTITUTION_TIER1` | Tier 1 constitution rule violated — output must be rejected |
| `ERR_CONSTITUTION_TIER2` | Tier 2 constitution rule violated — major revision required |
| `WARN_CONSTITUTION_TIER3` | Tier 3 constitution advisory — minor revision recommended |

---

## Vault Errors

| Code | Description |
|---|---|
| `ERR_VAULT_WRITE_FAIL` | Cannot write note to vault |
| `ERR_VAULT_READ_FAIL` | Cannot read note from vault |
| `ERR_VAULT_AMNESIA` | Note not retrievable after write |
| `ERR_VAULT_SCHEMA_INVALID` | Frontmatter fails schema validation |
| `ERR_VAULT_CONTRADICTION` | New note contradicts existing finding |

---

## Provider Errors

| Code | Description |
|---|---|
| `ERR_PROVIDER_UNAVAILABLE` | LLM provider health check failed |
| `ERR_PROVIDER_RATE_LIMITED` | Provider rate limit exceeded |
| `ERR_PROVIDER_TIMEOUT` | Provider response timeout |
| `ERR_PROVIDER_INVALID_RESPONSE` | Provider response malformed |

---

## Verification Errors

| Code | Description |
|---|---|
| `ERR_VERIFY_GATE_FAIL` | Verification gate rejected output |
| `ERR_VERIFY_HIDDEN_ASSUMPTION` | Undisclosed assumption detected |
| `ERR_CONTRADICTION_DETECTED` | Contradiction gate found conflicting claims |
| `WARN_CONFIDENCE_MISMATCH` | Claimed confidence exceeds evidence quality |
| `WARN_ADVERSARIAL_CHALLENGE` | Adversarial verifier raised unresolved challenge |

---

## System Errors

| Code | Description |
|---|---|
| `ERR_SYSTEM_UNKNOWN` | Unexpected internal error |
| `ERR_SYSTEM_LOOP_GUARD` | Max loop iterations exceeded |
| `ERR_SYSTEM_CONFIG_INVALID` | Configuration failed validation |

---

## Version History

| Version | Changes |
|---|---|
| v1 | Initial frozen catalog |
| v1.1 | Added Tool Assembly error codes (ERR_TOOL_ASSEMBLY_*, WARN_TOOL_ASSEMBLY_*) and Constitution error codes (ERR_CONSTITUTION_*) |

# Librarian — SKILL Definition

**Agent ID:** `librarian`
**Domain:** Memory Operations
**Current Level:** Novice (Level 1)

---

## Capability Definition

The Librarian manages all memory operations: intake, retrieval, gap detection,
amnesia check, and Supermemory integration. It is the gatekeeper between
the live blackboard and the persistent Obsidian vault.

### Primary Capabilities

| Capability | Status |
|---|---|
| Note intake (classify + store) | Active (MVP) |
| Retrieval (semantic + keyword) | Active (MVP) |
| Gap detection | Active (MVP) |
| Amnesia check | Active (MVP) |
| Pathway strength management | Active (MVP) |
| Supermemory hybrid search | Active (MVP) |
| Entity linking (auto-linker) | Active (MVP) |
| Note decay / consolidation | Planned (V1) |

### Tools Allowed

```yaml
tools_allowed: []  # No external tool calls — vault operations only
```

### Mandatory Output Fields

```yaml
operation: "intake|retrieval|gap_detection"
notes_written: []       # For intake
notes_retrieved: []     # For retrieval
gaps_identified: []     # For gap_detection
amnesia_flags: []       # Any notes with pathway_strength < 0.3
provenance: "vault_read|vault_write"
confidence: 1.0         # Deterministic operation — always 1.0
assumptions:
  - "Vault index is current (last updated < 24h)"
what_would_falsify: "Vault write fails or index becomes stale"
```

---

## Learned Strategies

See `learned/strategies.jsonl`. Current: 0 entries.

---

## Known Failure Patterns

- **Stale index**: Gap index not updated → missed gap detection
- **Duplicate notes**: Same finding written twice with different IDs
- **Broken links**: Entity registry out of sync with vault notes

---

## Output Contract (FROZEN v1)

```yaml
operation: "intake|retrieval|gap_detection"
notes_written: []
notes_retrieved: []
gaps_identified: []
amnesia_flags: []
provenance: "vault_read|vault_write"
confidence: 1.0
assumptions:
  - "Vault index is current (last updated < 24h)"
  - "Note IDs are globally unique"
  - "Entity registry reflects latest vault state"
what_would_falsify: "Vault write fails or index becomes stale"
```

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Core intake, retrieval, gap detection |
| 2 | Apprentice | 0.40–0.59 | Semantic search, pathway strength management |
| 3 | Journeyman | 0.60–0.74 | Decay/consolidation, entity linking |
| 4 | Expert | 0.75–0.89 | Cross-vault consistency, multi-agent memory sync |
| 5 | Master | 0.90–1.00 | Adaptive memory architecture, amnesia prediction |

---

## Escalation Flags

- Vault write failure: **HALT** — escalate to forge_maintenance_orchestrator
- Gap index age > 48h: warn and request re-index before gap detection
- Pathway strength < 0.1 on > 10% of notes: alert degraded memory state

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current defaults.

- Retrieval strategy: semantic-first, keyword fallback
- Confidence threshold: 1.0 (deterministic vault operations)
- Max retrieval results: 20 per query

---

## References

- Obsidian Vault Integration Spec: `docs/specs/vault-integration.md`
- Memory Architecture: `docs/architecture/memory-system.md`
- Supermemory API: `docs/integrations/supermemory.md`

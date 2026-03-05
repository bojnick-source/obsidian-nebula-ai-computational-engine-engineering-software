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

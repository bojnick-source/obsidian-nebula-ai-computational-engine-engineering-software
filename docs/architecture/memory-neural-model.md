# Memory Neural Model

> How FORGE's Obsidian-based neural memory works conceptually and operationally.

---

## Core Concept

FORGE's memory is modeled as a weighted knowledge graph stored in Obsidian markdown notes. Each note is a typed knowledge node with:
- Structured YAML frontmatter (schema-validated)
- Human-readable content
- Links to related notes (the "neural" connections)
- Pathway strength (how often this note is accessed/confirmed)
- Provenance (source attribution)
- Confidence score
- Gap flags

The graph is not static. It strengthens on confirmation, weakens on disuse (decay detection), and routes contradictions to a disputed note tier.

---

## Note Types

| Type | Purpose |
|---|---|
| `finding` | Established engineering result with provenance |
| `derivation` | Step-by-step mathematical derivation |
| `decision` | Design decision with rationale and alternatives |
| `gap` | Known unknown — unresolved question that needs investigation |
| `synthesis` | Higher-order note generated from a cluster of findings |
| `agent-thinking` | Reasoning record from a specific agent on a specific task |
| `ilc-link` | Inter-domain link candidate (V1) |

---

## Memory Operations

### Intake
1. Agent output (verified) → schema validation
2. Frontmatter completion (type, domain, confidence, provenance, trace_id)
3. Placement in vault directory structure
4. Back-links established to related notes

### Retrieval
1. Domain filter applied (e.g., `domain: mechanical_engineering`)
2. Context filter applied (e.g., `component: motor_mount_bracket`)
3. Pathway strength incremented on access
4. Context package assembled for specialist

### Gap Detection
1. After each specialist run, gap flags are scanned
2. Existing gap notes checked for duplicates
3. New gap notes created for unresolved flags
4. Source attribution recorded

### Strengthening
1. New evidence for an existing finding → merge evidence
2. Confidence score updated
3. Provenance appended
4. Last-confirmed timestamp updated

### Contradiction Handling
1. New claim conflicts with existing finding
2. Old note versioned (renamed with `_superseded` suffix)
3. Disputed note created linking both versions
4. Contradiction flag raised → Overwatch/human review
5. Resolution recorded when resolved

### Synthesis
1. Cluster of related findings exceeds threshold (e.g., 5 notes, same domain)
2. Synthesis note proposed
3. Transitive confidence rule applied (synthesis confidence ≤ min of sources)
4. All source notes linked

### Decay Detection
1. Notes not accessed in >N days flagged as potentially stale
2. Low-use notes flagged for review
3. No auto-delete — human decision required
4. Stale index updated: `forge-vault/indexes/stale-index.md`

---

## Pathway Strength

A numeric weight on each note (0.0–1.0) representing how well-established it is:
- Incremented on each access (retrieval, confirmation, synthesis citation)
- Used to rank retrieval results
- Low pathway_strength notes flagged for decay review

---

## Amnesia Check

After every vault write, a retrieval is attempted immediately to confirm the note is accessible. Failure triggers pipeline halt. See `docs/architecture/core-loop.md` Phase 8.

---

## Schema Reference

- Frontmatter schema: `forge-memory/schemas/vault_frontmatter.schema.yaml`
- Note types: `forge-memory/schemas/note_types.yaml`
- Agent thinking schema: `forge-memory/schemas/agent_thinking.schema.yaml`
- ILC link schema: `forge-memory/schemas/ilc_link.schema.yaml`

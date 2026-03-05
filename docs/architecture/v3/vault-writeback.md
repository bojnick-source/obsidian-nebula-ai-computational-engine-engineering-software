# Vault Write-Back Design (Context 1C)

> Every FORGE run produces structured Obsidian vault notes with auto-linking.
> Human interface: Obsidian Graph View + Dataview queries.
> Agent interface: Supermemory sub-300ms hybrid vector + BM25 retrieval.

---

## Vault Directory Structure (v3 extended)

```
forge-vault/
├── 00-Meta/
│   ├── templates/          # Note templates (finding, derivation, etc.)
│   ├── mocs/               # Auto-generated Maps of Content
│   └── entity_registry.yaml # Entity → vault path mapping for auto-linking
├── 01-Projects/
│   ├── aladdin-3b/
│   ├── project-vanguard/
│   └── phoenix/
├── 02-Materials/           # Canonical material property cards
│   ├── 6061-T6-aluminum.md
│   ├── ti-6al-4v.md
│   └── ...
├── 03-Standards/           # Engineering standards references
│   ├── ASME-BPVC-VIII.md
│   ├── Eurocode-3.md
│   └── ...
├── 04-Analyses/            # All analysis results (primary FORGE output)
│   └── {project}/{component}/{run_id}/
├── 05-Equations/           # Key equations as atomic notes
├── 06-Methods/             # Analysis methodology notes
├── 07-Agent-Logs/          # Raw session traces (agent-thinking notes)
└── 08-MOCs/                # Auto-generated indexes
```

---

## Note Frontmatter (extended from v1 schema)

V3 adds engineering-specific fields on top of the base vault frontmatter schema:

```yaml
---
# Base fields (from vault-frontmatter-schema.md v1)
id: uuid-v4
type: finding
domain: mechanical_engineering
trace_id: uuid-v4
agent_id: me_specialist
agent_version: "1.0.0"
confidence: 0.87
pathway_strength: 0.1

# V3 additions
forge_level: 3            # Agent level that produced this (1-5)
analysis_type: linear_static_fea
project: aladdin-3b
component: motor_mount_bracket
material: 6061-T6-aluminum    # links to 02-Materials/ note
standard_ref: ASME-BPVC-VIII  # links to 03-Standards/ note
status: validated             # draft → validated → superseded
session_id: forge-042
run_id: forge-042
supersedes: null              # links to superseded note if applicable

# Episodic memory link
episode_id: ep-042            # links to episodic memory store
quality_score: 0.87           # quality evaluator score
---
```

---

## Auto-Linking Pipeline

```python
# forge-output/src/forge_output/vault_writer.py

class VaultWriter:
    def __init__(self, vault_path: str, entity_registry_path: str,
                 supermemory_client=None):
        self.vault_path = Path(vault_path)
        self.entities = yaml.safe_load(open(entity_registry_path))
        self.sm = supermemory_client

    def write_note(self, note: VaultNote) -> str:
        """Write a note, auto-link entities, find semantically similar notes."""
        content = self._render_template(note)

        # Pass 1: entity registry auto-linking
        content = self._insert_entity_links(content, note.domain)

        # Pass 2: semantic similarity linking (top 5 similar existing notes)
        if self.sm:
            similar = self.sm.search(q=note.content_summary, limit=5,
                                     container_tag="forge")
            content = self._append_related_section(content, similar)

        # Write note
        note_path = self._resolve_path(note)
        note_path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter.dump(note.metadata, content, note_path.open("w"))

        # Simultaneously store in Supermemory for agent retrieval
        if self.sm:
            self.sm.add(content=note.knowledge_summary,
                        container_tag="forge",
                        metadata={"note_id": note.id, "domain": note.domain,
                                  "trace_id": note.trace_id})

        # Amnesia check
        return self._amnesia_check(note.id, note_path)
```

### Entity Registry Format

```yaml
# forge-vault/00-Meta/entity_registry.yaml
entities:
  materials:
    "6061-T6": "02-Materials/6061-T6-aluminum.md"
    "Ti-6Al-4V": "02-Materials/ti-6al-4v.md"
    "Inconel 718": "02-Materials/inconel-718.md"

  standards:
    "ASME BPVC": "03-Standards/ASME-BPVC-VIII.md"
    "Eurocode 3": "03-Standards/Eurocode-3.md"
    "FAR 23": "03-Standards/FAR-23.md"

  equations:
    "von Mises": "05-Equations/von-mises-stress.md"
    "Tresca": "05-Equations/tresca-criterion.md"
    "Euler buckling": "05-Equations/euler-column-buckling.md"

  projects:
    "Aladdin-3B": "01-Projects/aladdin-3b/MOC.md"
    "Vanguard": "01-Projects/project-vanguard/MOC.md"
    "Phoenix": "01-Projects/phoenix/MOC.md"
```

---

## Supermemory Integration

Supermemory serves as the agent-optimized retrieval layer:
- Sub-300ms recall latency
- Hybrid vector + BM25 retrieval (vector weight 0.7, BM25 weight 0.3)
- Container tagging by project and domain

```python
import supermemory

client = supermemory.Supermemory(api_key=os.environ["SUPERMEMORY_API_KEY"])

# On vault write: store knowledge unit
client.add(
    content=knowledge_summary,
    container_tag=f"forge/{project}/{domain}",
    metadata={"note_id": note_id, "confidence": confidence,
              "trace_id": trace_id, "analysis_type": analysis_type}
)

# Before run: retrieve relevant past knowledge
results = client.search(
    q=task_description,
    container_tag=f"forge/{project}",
    limit=5
)
# Returns: [{content, metadata, score}, ...]
```

---

## Dataview Queries (built-in)

Pre-built queries in `00-Meta/mocs/`:

```dataview
// All validated FEA analyses for Aladdin-3B sorted by confidence
TABLE confidence, analysis_type, agent_id, forge_level
FROM "04-Analyses/aladdin-3b"
WHERE status = "validated" AND analysis_type = "linear_static_fea"
SORT confidence DESC
```

```dataview
// All open gaps for current project
TABLE domain, component, gap_flags
FROM "04-Analyses"
WHERE type = "gap" AND status != "resolved"
SORT created_at DESC
```

```dataview
// Agent performance trends (last 30 days)
TABLE agent_id, count(rows) as runs, avg(confidence) as avg_conf
FROM "04-Analyses"
WHERE created_at >= date(today) - dur(30 days)
GROUP BY agent_id
SORT avg_conf DESC
```

---

## Versioning Policy

When a new analysis supersedes an old one:
1. New note carries: `supersedes: [[old-note-id]]`
2. Old note gets: `status: superseded`, `superseded_by: [[new-note-id]]`
3. Dataview default queries filter out `status: superseded` notes
4. Git history preserves all versions

Contradictions (same quantity, different values):
1. New note carries: `disputes: [[old-note-id]]`, `dispute_status: open`
2. Old note gets: `disputes: [[new-note-id]]`, `dispute_status: open`
3. Contradiction index updated: `forge-vault/indexes/contradiction-index.md`
4. Overwatch flag set — human review required

# Three-Tier Memory Hierarchy

> Maps ReMe memory types to FORGE components.
> Critical invariant: Working Memory → (quality gate) → Task/Personal Memory → Supermemory.

---

## Memory Type Map

| ReMe Memory Type | FORGE Component | TTL | Purpose |
|---|---|---|---|
| **Working Memory** | Blackboard | Single run | Current context, inter-agent messages, active tool results |
| **Task Memory** | Obsidian `04-Analyses/` | Weeks–months | Procedural strategies, success/failure patterns, comparative insights |
| **Personal Memory** | Obsidian `01-Projects/` | Permanent | Project context, user preferences, domain conventions |
| **Tool Memory** | `forge-learning/tool_memory/` | Permanent | Historical tool performance, parameter optimization, dynamic guidelines |

---

## Working Memory: Blackboard with Message Offload

The blackboard doubles as Working Memory. For long-running tasks (12-step pipeline, 68+ agents), context accumulates to tens of thousands of tokens. ReMe's **message offload/reload** pattern reduces this by 81% (95K → 18K tokens) with quality improvement.

### Offload policy

```python
# forge-learning/src/forge_learning/working_memory.py
class WorkingMemoryManager:
    MAX_CONTEXT_TOKENS = 20_000  # hard limit before offload triggers

    def offload_to_task_memory(self, blackboard: Blackboard,
                                quality_evaluator: QualityEvaluator) -> None:
        """
        When context exceeds threshold:
        1. Score all blackboard entries by recency + relevance
        2. Offload low-scoring entries to task memory (if quality gate passes)
        3. Keep summary + pointers in working memory
        """
        entries = blackboard.get_all_entries()
        token_count = estimate_tokens(entries)

        if token_count > self.MAX_CONTEXT_TOKENS:
            # Sort by recency × relevance score (lowest = offload first)
            scored = self._score_entries(entries)
            to_offload = scored[:len(scored)//2]  # offload bottom half

            for entry in to_offload:
                if quality_evaluator.score(entry) >= 0.8:
                    self._write_to_task_memory(entry)
                blackboard.replace_with_pointer(entry.field,
                                                 entry.summary,
                                                 entry.task_memory_ref)
```

---

## Task Memory: Obsidian Vault (04-Analyses)

Stores procedural knowledge extracted from successful runs:

- Successful analysis strategies: "k-epsilon model works for turbulent pipe flow Re>10000"
- Tool parameter optimizations: "GMSH Delaunay + max_element_size=2mm → stable CalculiX mesh"
- Failure patterns: "Point load application at re-entrant corner → stress singularity"
- Comparative insights: "Ti-6Al-4V reduces weight by 40% vs. 6061-T6 at same strength"

Each strategy note has a `reuse_count` frontmatter field, incremented every time it appears in a new run's context. This drives the `strategy_reuse_rate` metric.

---

## Tool Memory: Dynamic Guidelines

```
forge-learning/tool_memory/
├── calculix/
│   ├── performance_history.jsonl   # Latency, success rate per mesh size
│   ├── parameter_prefs.yaml        # Optimized solver parameters
│   └── guidelines.md               # Dynamically updated best practices
├── gmsh/
│   ├── performance_history.jsonl
│   └── parameter_prefs.yaml
└── supermemory/
    └── retrieval_stats.jsonl       # Query→result quality feedback
```

### Tool performance tracking

```python
# After each tool invocation, record to performance history
tool_record = {
    "ts": now_iso8601(),
    "tool_id": "calculix",
    "run_id": run_id,
    "input_summary": {"mesh_elements": 22500, "analysis_type": "linear_static"},
    "duration_ms": 8340,
    "status": "success",
    "quality_score": 0.91,  # from quality evaluator post-run
    "parameters": solver_params
}
```

Guidelines are re-generated from performance history every 10 runs using an LLM summarizer, then added to the agent context for the relevant tool calls.

---

## Memory Consolidation (Sleep Phase)

Scheduled as a Temporal cron workflow (nightly):

```
1. Replay recent episodes (sliding 7-day window)
2. Find hidden connections (embedding similarity across episodes)
3. Consolidate episodic → semantic:
   - Specific run details → general patterns
   - Example: "Run #42: mesh density 2mm gave 4.7% stress difference on refinement"
     → Pattern: "Motor mount bracket requires ≤2mm mesh for convergence"
4. FSRS-6 utility scoring:
   utility = success_rate × recency_weight × retrieval_frequency
5. Prune memories below utility threshold (default: 0.2)
6. Reinforce frequently-retrieved successful memories
```

### FSRS-6-Inspired Utility Function

```python
def compute_utility(memory: Memory) -> float:
    success_rate = memory.successful_retrievals / max(memory.total_retrievals, 1)
    recency_weight = math.exp(-0.1 * days_since_last_access(memory))
    retrieval_frequency = min(memory.total_retrievals / 10.0, 1.0)  # cap at 1.0
    return success_rate * recency_weight * retrieval_frequency

PRUNE_THRESHOLD = 0.2
```

---

## Contradiction Handling in Memory

Contradictory learnings are **not overwritten** — both versions are kept with metadata:

```yaml
# In conflict note frontmatter
conflict_type: "material_property_disagreement"
claim_a: "6061-T6 yield strength: 276 MPa (ASM Handbook 2015)"
claim_b: "6061-T6 yield strength: 255 MPa (measured, run forge-051)"
resolution: "Use 255 MPa for Aladdin-3B (measured, closer to actual batch)"
resolution_confidence: 0.78
dispute_status: "resolved"
```

The quality evaluator determines which version applies in future contexts based on context similarity.

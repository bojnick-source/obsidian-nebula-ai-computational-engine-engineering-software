# Episodic Memory System (2A)

> Self-learning from past FORGE runs. Gated by strict quality evaluator.
> Critical: only episodes scoring ≥0.8 committed to medium-term memory.

---

## Post-Run Capture Schema

```yaml
# Saved to forge-learning/episodes/{run_id}.yaml after every run
episode:
  run_id: forge-042
  task_description: "Thermal analysis of heat exchanger tube bundle"
  project: aladdin-3b
  component: motor_mount_bracket
  timestamp: "2026-03-05T14:30:00Z"

  agents:
    - id: me_specialist
      version: "1.0.0"
      level: 3
      role: lead
      tokens_used: 4820
      duration_ms: 12400

  trace:
    - {agent: orchestrator, phase: intake, action: task_classification,
       duration_ms: 120}
    - {agent: librarian, phase: memory_preflight, action: retrieve,
       notes_retrieved: 3, duration_ms: 280}
    - {agent: me_specialist, phase: specialist, action: structural_analysis,
       tokens_in: 3200, tokens_out: 1620, duration_ms: 12400}
    - {tool: gmsh, phase: tool_execution, action: mesh_generation,
       elements: 22500, duration_ms: 4100}
    - {tool: calculix, phase: tool_execution, action: linear_static_fea,
       duration_ms: 8340}
    - {phase: verification, gates_passed: [contract, unit, dimensional, provenance],
       gates_failed: []}

  outcome:
    status: complete
    quality_score: 0.87        # set by quality evaluator
    evaluator: quality_evaluator_v1
    vault_notes_written: 2
    total_cost_usd: 0.34
    total_tokens: 8440

  learnings:
    success_patterns:
      - "6061-T6 yield strength from ASM Handbook accepted by provenance gate"
      - "GMSH Delaunay algorithm stable for prismatic bracket geometry"
      - "CalculiX linear static converges in 1 pass for this load case"
    failure_patterns: []
    reusable_strategies:
      - "Motor mount bracket: mesh at ≤2mm for <5% stress difference on refinement"
      - "Fixed-free cantilever BCs work for motor mount with bolt pattern"
    tool_parameter_findings:
      - tool: gmsh
        param: max_element_size_mm
        value: 2.0
        outcome: "22500 elements, good quality (min Jacobian 0.82)"
    gaps_identified:
      - "Dynamic load analysis not performed — fatigue life unknown"

  embedding: []  # populated by SPECTER2 or sentence-transformers
```

---

## Quality Evaluator

The single most critical v3 component. An LLM-as-judge configured with the Engineering Constitution.

```python
# forge-learning/src/forge_learning/quality_evaluator.py

class QualityEvaluator:
    """
    Evaluates FORGE run episodes against the Engineering Constitution.
    Returns a quality score [0.0, 1.0].
    Only episodes scoring >= COMMIT_THRESHOLD are committed to memory.
    """

    COMMIT_THRESHOLD = 0.8

    def __init__(self, llm_client, constitution_path: str):
        self.llm = llm_client
        self.constitution = yaml.safe_load(open(constitution_path))

    def evaluate(self, episode: Episode) -> EvaluationResult:
        """Run episode through Engineering Constitution evaluation."""
        prompt = self._build_evaluation_prompt(episode)
        response = self.llm.call(prompt, temperature=0.0)  # deterministic
        score = self._parse_score(response)

        return EvaluationResult(
            episode_id=episode.run_id,
            quality_score=score,
            should_commit=score >= self.COMMIT_THRESHOLD,
            gate_results=self._extract_gate_results(response),
            reasoning=response.text
        )

    def _build_evaluation_prompt(self, episode: Episode) -> str:
        return f"""
You are the FORGE Quality Evaluator. Assess this engineering analysis episode
against the Engineering Constitution.

Score from 0.0 to 1.0 where:
  1.0 = All constitution tiers satisfied, novel insights, excellent provenance
  0.8 = All Tier 1-3 requirements met, good provenance, useful strategies
  0.6 = Tier 1-2 met, some Tier 3 gaps, provenance acceptable
  <0.6 = Tier 1 or 2 violations — DO NOT COMMIT TO MEMORY

Engineering Constitution Tier 1 (inviolable):
{yaml.dump(self.constitution['tier_1'])}

Engineering Constitution Tier 2 (physics):
{yaml.dump(self.constitution['tier_2'])}

Engineering Constitution Tier 3 (engineering):
{yaml.dump(self.constitution['tier_3'])}

Episode to evaluate:
{episode.to_evaluation_summary()}

Output JSON: {{"score": float, "tier_violations": [], "reasoning": "..."}}
"""
```

---

## Experience Retrieval (Hybrid Search)

```python
# Before each new run: retrieve top-5 relevant past episodes
def retrieve_relevant_episodes(task_description: str,
                                supermemory_client) -> list[EpisodeSummary]:
    """
    Hybrid vector (0.7) + BM25 (0.3) retrieval via Supermemory.
    Returns top 5 episodes with their reusable_strategies.
    """
    results = supermemory_client.search(
        q=task_description,
        container_tag="forge/episodes",
        limit=5
    )
    return [EpisodeSummary.from_supermemory(r) for r in results]
```

Injected into agent context as:
```
## Relevant past analyses (from FORGE memory):
1. Motor mount bracket linear static FEA (forge-042, confidence 0.87)
   Strategy: "Mesh at ≤2mm for convergence; Fixed-free BCs at bolt pattern"
2. Aluminum bracket fatigue analysis (forge-039, confidence 0.82)
   Strategy: "R=-1 stress ratio; Morrow mean stress correction for 6061-T6"
```

---

## Agent Leveling Criteria (Voyager-inspired)

| Level | Title | Unlock Criteria |
|---|---|---|
| 1 | Novice | — (default) |
| 2 | Competent | 10 tasks with quality_score ≥0.80; can read task memory |
| 3 | Proficient | Pattern recognition across 3+ problem types; can write task memory |
| 4 | Expert | 5 novel problems solved by transferred knowledge; strategies reused 10+ times |
| 5 | Master | Systemic improvements adopted system-wide; memory curation rights |

Level is recomputed from a **20-run sliding window** of metrics:
- Task success rate (quality_score ≥0.80)
- Strategy reuse rate (how often this agent's strategies appear in others' context)
- Token efficiency trajectory (tokens/task trending ↓)
- Novel insight rate (new patterns not in existing memory)

Level is stored in the agent card and used for routing priority.

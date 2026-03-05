# Agent Leveling System

> Five-level competence model. Levels unlock capabilities and memory access.
> Inspired by Voyager (Microsoft Research): 3.3× unique skills, 15.3× faster milestones.

---

## Level Definitions

| Level | Title | Memory Access | Unlock Criteria |
|---|---|---|---|
| 1 | Novice | Working memory only | Default — all new agents |
| 2 | Competent | Read task memory | 10 tasks quality_score ≥0.80 |
| 3 | Proficient | Write task memory | Pattern recognition across 3+ problem types; 3 novel problems solved |
| 4 | Expert | Full memory (read/write/personal) | Own strategies reused 10+ times by other agents |
| 5 | Master | Memory curation rights | Systemic improvement adopted system-wide |

---

## Level Computation

Recomputed from a **20-run sliding window** after every run:

```python
def compute_agent_level(agent_id: str,
                         recent_episodes: list[Episode]) -> int:
    """
    Returns new level based on 20-run sliding window metrics.
    """
    agent_episodes = [e for e in recent_episodes
                      if agent_id in [a.id for a in e.agents]]

    if len(agent_episodes) < 5:
        return 1  # insufficient data

    success_rate = sum(1 for e in agent_episodes
                       if e.outcome.quality_score >= 0.80) / len(agent_episodes)
    strategy_reuse = compute_strategy_reuse_rate(agent_id, recent_episodes)
    token_efficiency_trend = compute_token_efficiency_trend(agent_id, agent_episodes)
    novel_insight_rate = compute_novel_insight_rate(agent_id, recent_episodes)

    # Composite score
    score = (0.40 * success_rate +
             0.30 * min(strategy_reuse, 1.0) +
             0.20 * token_efficiency_trend +  # positive = improving
             0.10 * novel_insight_rate)

    # Level thresholds
    if score >= 0.90 and strategy_reuse >= 0.5:
        return 5
    elif score >= 0.80 and strategy_reuse >= 0.3:
        return 4
    elif score >= 0.70:
        return 3
    elif success_rate >= 0.80:
        return 2
    else:
        return 1
```

---

## SKILL.md Format

Each agent has a `SKILL.md` file defining its capabilities (DeerFlow/Anthropic pattern). Under 500 lines. Has a `learned/` subdirectory for accumulated strategies.

```
forge-agents/
  me_specialist/
    SKILL.md                 # Core capability definition (≤500 lines)
    references/
      structural-mechanics.md
      fatigue-analysis.md
    templates/
      fea_output_template.md
    learned/
      strategies.jsonl       # Successful strategies (appended post-run)
      tool_prefs.yaml        # Optimized tool parameters
      failure_patterns.jsonl # Failure modes encountered
```

### SKILL.md Structure

```markdown
# ME Specialist — SKILL.md

## Role
Mechanical engineering analysis specialist for structural, fatigue,
vibration, and thermal-mechanical problems.

## Core Capabilities
- Structural analysis (linear/nonlinear static, dynamic)
- Fatigue analysis (S-N, ε-N, Morrow mean stress correction)
- Vibration analysis (modal, harmonic, random)
- Thermal-mechanical coupling

## Workflows
### Structural Analysis Workflow
1. Review task constraints and load cases
2. Retrieve relevant past analyses from vault
3. Identify applicable failure modes
4. Set up analysis: material, geometry, BCs, loads
5. Request mesh generation (GMSH) + FEA (CalculiX)
6. Validate results against constitution (Tier 1-3)
7. Compare with analytical solution where applicable
8. Document assumptions explicitly

## Best Practices
(See learned/strategies.jsonl for empirically discovered practices)

## References
- ASM Handbook Vol. 19: Fatigue and Fracture
- Peterson's Stress Concentration Factors (3rd ed.)
- Roark's Formulas for Stress and Strain (8th ed.)
- Shigley's Mechanical Engineering Design (10th ed.)

## Output Contract
See docs/contracts/agent-output-contract.md (output_type: analysis)
```

---

## Capability Unlocks by Level

| Capability | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|
| Execute predefined workflows | ✓ | ✓ | ✓ | ✓ | ✓ |
| Select from existing strategies | | ✓ | ✓ | ✓ | ✓ |
| Read task memory (vault retrievals) | | ✓ | ✓ | ✓ | ✓ |
| Adapt strategies to novel contexts | | | ✓ | ✓ | ✓ |
| Write task memory (strategies.jsonl) | | | ✓ | ✓ | ✓ |
| Generate new strategies | | | | ✓ | ✓ |
| Mentor lower-level agents (strategy injection) | | | | ✓ | ✓ |
| Curate / prune memory | | | | | ✓ |
| Propose systemic improvements | | | | | ✓ |

---

## Level Stored in Agent Card

```yaml
# forge-agents/registry/agent_cards/me.yaml (excerpt)
id: me_specialist
version: "1.0.0"
level: 1          # current computed level (updated post-run)
level_history:    # sliding window data
  - run_id: forge-042
    quality_score: 0.87
    strategy_reuse: 0.2
    token_efficiency: 0.85
  - run_id: forge-039
    quality_score: 0.81
    strategy_reuse: 0.1
    token_efficiency: 0.90
```

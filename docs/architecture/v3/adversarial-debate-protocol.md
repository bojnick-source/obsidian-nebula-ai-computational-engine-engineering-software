# Adversarial Debate Protocol (2C)

> Structured 4-phase debate with hard cap of 3 rounds.
> Anti-sycophancy rules enforced at protocol level.
> Computable checks never enter debate — they are deterministic functions.

---

## The Sycophancy Problem

Research finding: **sycophancy is the #1 failure mode in multi-agent debate** ("Talk Isn't Always Cheap," Wynn et al., 2025).
- Agents agree reflexively rather than challenge flawed reasoning
- Introducing a weaker model into debate can *degrade* the stronger model
- Simple majority voting enables "tyranny of the majority"

This protocol explicitly counters all three failure modes.

---

## Four-Phase Debate Protocol

### Phase 1: Independent Analysis

```
RULE: Both specialist and antagonist solve in isolation — no cross-contamination.
```

Both agents receive the same task description, constraints, and vault context. They produce independent outputs. Neither sees the other's output during this phase.

**Why:** Cross-contamination in Phase 1 is the primary sycophancy injection point.

### Phase 2: Structured Critique

```
RULE: Critiques MUST cite specific numerical values + reference a physical law
      + provide an alternative. Vague objections rejected by protocol parser.
```

Each agent critiques the other's Phase 1 output using the required critique format:

```yaml
critique:
  target_claim: "Max von Mises stress: 142 MPa (me_specialist)"
  objection: "Stress concentration at fillet radius not captured. Using r=0.5mm
              fillet, Kt ≈ 2.8 (Peterson, Stress Concentration Factors, 3rd ed.,
              Fig. 4-6). Actual peak stress ≈ 142 × 2.8 = 398 MPa > σ_yield."
  severity: fatal                 # fatal | major | minor
  physical_law: "Stress concentration theory (Peterson)"
  alternative: "Use FEA mesh refinement at fillet, min element size ≤ r/5 = 0.1mm"
  numerical_evidence: "Kt=2.8 from Peterson, r/d=0.025, D/d=1.5"
```

Protocol parser **rejects** critiques that:
- Are fewer than 50 words
- Do not contain a numerical value
- Do not cite a source (author, standard, or equation name)
- Consist only of "this is wrong" variants without substance

### Phase 3: Evidence Response

```
RULE: Each round must introduce NEW evidence — not restate.
RULE: Confidence tracked per round. If both decrease: stop, escalate.
```

Each agent responds to critiques with:
- Calculations showing the critique is wrong (if contested)
- Acceptance + corrected analysis (if critique is valid)
- Additional references supporting their position

Confidence tracking:
```python
if (round > 1 and
    agent_a.confidence_round_n < agent_a.confidence_round_n_minus_1 and
    agent_b.confidence_round_n < agent_b.confidence_round_n_minus_1):
    # Both agents losing confidence = genuine uncertainty, not disagreement
    stop_debate()
    escalate_to_human_review()
```

### Phase 4: Arbiter Synthesis

```
ROUTE: Math disagreement → Math arbiter
       Physics disagreement → Physics arbiter
       Methodological disagreement → "run both, compare"
```

The cross-class arbiter (an LLM configured with the Engineering Constitution) synthesizes:

1. Lists all unresolved objections by severity
2. For `fatal` objections: must be resolved before proceeding
3. For `major` objections: documented in output, flagged for human review
4. For `minor` objections: documented in output, pipeline continues

---

## Anti-Degeneration Rules

| Rule | Implementation |
|---|---|
| **Hard round cap: 3** | Enforced by debate lifecycle controller — no round 4 ever |
| **Novelty requirement** | Protocol parser checks that each response introduces ≥1 new citation or calculation not in previous rounds |
| **Token budget per round** | Each agent: max 2,000 tokens per critique/response round |
| **Confidence-weighted decision** | Resolution uses confidence-weighted synthesis, not simple majority |
| **Independent Phase 1** | No cross-contamination of reasoning before critique begins |
| **Vague objection rejection** | Protocol parser enforces structured critique format |

---

## Debate Lifecycle State Machine

```
                    ┌─────────────────┐
                    │   INDEPENDENT   │
                    │    ANALYSIS     │
                    └────────┬────────┘
                             │ both outputs ready
                    ┌────────▼────────┐
                    │   STRUCTURED    │
              ┌─────│    CRITIQUE     │
              │     └────────┬────────┘
              │              │ critiques exchanged
              │     ┌────────▼────────┐
              │     │    EVIDENCE     │
              │     │    RESPONSE     │◄──── round 2, 3 (max)
              │     └────────┬────────┘
              │              │ responses complete OR
confidence    │              │ both confidence declining
declining     │     ┌────────▼────────┐
              └────►│    ARBITER      │
                    │    SYNTHESIS    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        RESOLVED       ESCALATED      "RUN BOTH"
        (pipeline     (human review)  (compare outputs)
        continues)
```

---

## Debate Output Format

```yaml
debate_result:
  run_id: forge-042
  round_count: 2
  outcome: resolved           # resolved | escalated | run_both

  specialist_final:
    agent_id: me_specialist
    confidence: 0.82
    key_claims: [...]
    accepted_critiques:
      - "Stress concentration at fillet — recalculated with Kt=2.8"

  antagonist_final:
    agent_id: materials_antagonist
    confidence: 0.75
    objections_remaining: []  # empty = all resolved

  arbiter_synthesis:
    resolved_items: [...]
    flagged_for_human_review: []
    run_both_cases: []

  adversarial_log_ref: "forge-vault/engineering/adversarial-logs/forge-042.md"
```

---

## What Is Never Debated

These checks run as deterministic Python functions before debate begins. If they fail, debate is skipped and the error is returned immediately:

- Reaction force equilibrium (FEA)
- Energy balance (FEA)
- Mesh convergence check (GCI < 5%)
- Stress singularity detection
- CFD residual convergence
- Mass conservation at boundaries
- y+ appropriateness for wall treatment

**Rationale:** These are computable, not arguable. Routing them through LLM debate wastes tokens and risks a bad agent talking a good one into accepting a wrong answer.

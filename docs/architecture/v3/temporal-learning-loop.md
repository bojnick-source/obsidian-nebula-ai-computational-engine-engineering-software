# Temporal Learning Loop (2D)

> Crash-resistant durable execution via Temporal SDK.
> Every step checkpointed — long FEA/CFD runs survive crashes.
> Human-in-the-loop gates on confidence drop or vault contradiction.

---

## Learning Loop Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    FORGE Learning Loop                          │
│                                                                │
│  EXECUTE ──→ EVALUATE ──→ DISTILL ──→ GATE ──→ STORE ──→ NEXT │
│     │            │           │         │         │          │   │
│  12-step      Quality     Extract   Score     Obsidian   Query │
│  pipeline    evaluator   patterns   ≥0.8?    + Super-   vault  │
│  + debate    (Eng.       + compare   │ YES    memory   before  │
│  protocol   Constitution) w/ vault   │ NO→     │       next    │
│              + LLM-judge   knowledge  discard  │       run     │
│                                               │                │
│  ←──────── External Discovery (scheduled) ────┘                │
│  arXiv monitor, Semantic Scholar scan, Materials Project sync  │
└────────────────────────────────────────────────────────────────┘
```

---

## Temporal Workflow Definition

```python
# forge-learning/src/forge_learning/workflows/forge_run_workflow.py
from temporalio import workflow, activity
from datetime import timedelta

@workflow.defn
class ForgeRunWorkflow:
    """
    Durable execution of a complete FORGE run with learning loop.
    Every Activity is checkpointed — crash at any point resumes here.
    """

    @workflow.run
    async def run(self, task: ForgeTask) -> ForgeResult:
        # Phase 0-2: Core execution (all checkpointed)
        bb_init = await workflow.execute_activity(
            initialize_blackboard,
            task,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Retrieve relevant past episodes (Supermemory query)
        past_context = await workflow.execute_activity(
            retrieve_relevant_episodes,
            task.description,
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Phase 4: Specialist (may be long — LLM call)
        specialist_output = await workflow.execute_activity(
            run_specialist_phase,
            SpecialistInput(blackboard=bb_init, past_context=past_context),
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Phase 6: Tool execution (may be very long — FEA/CFD)
        tool_result = await workflow.execute_activity(
            run_tool_execution_phase,
            ToolInput(blackboard=specialist_output.blackboard),
            # CalculiX/OpenFOAM can run for hours
            start_to_close_timeout=timedelta(hours=4),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        # Phase 7: Verification (automated constitution checks first)
        automated_checks = await workflow.execute_activity(
            run_automated_constitution_checks,
            tool_result,
            start_to_close_timeout=timedelta(seconds=60)
        )

        if automated_checks.has_tier1_violation:
            # Tier 1 violation: halt immediately, no debate
            return ForgeResult.failed(
                error_code="ERR_CONSTITUTION_TIER1",
                detail=automated_checks.tier1_violation
            )

        # Phase 7b: LLM verification gates
        verification = await workflow.execute_activity(
            run_verification_gates,
            tool_result,
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Human-in-the-loop gate: pause if confidence drops below 0.7
        if verification.confidence < 0.7:
            await workflow.execute_activity(
                request_human_review,
                HumanReviewRequest(
                    run_id=task.run_id,
                    reason="confidence_below_threshold",
                    confidence=verification.confidence
                ),
                start_to_close_timeout=timedelta(hours=24)  # wait up to 24h
            )

        # Phase 8: Vault persistence
        vault_result = await workflow.execute_activity(
            run_vault_persistence,
            PersistenceInput(verification=verification),
            start_to_close_timeout=timedelta(minutes=2)
        )

        # Post-run: quality evaluation + learning
        quality_result = await workflow.execute_activity(
            evaluate_run_quality,
            EvaluationInput(run_id=task.run_id, vault_result=vault_result),
            start_to_close_timeout=timedelta(minutes=5)
        )

        if quality_result.should_commit:
            await workflow.execute_activity(
                commit_to_memory,
                quality_result,
                start_to_close_timeout=timedelta(minutes=5)
            )

        return ForgeResult.from_vault(vault_result, quality_result)
```

---

## Scheduled Workflows

### Daily Knowledge Discovery

```python
@workflow.defn
class DailyKnowledgeDiscoveryWorkflow:
    @workflow.run
    async def run(self) -> None:
        # arXiv RSS scan
        new_papers = await workflow.execute_activity(
            scan_arxiv_rss,
            categories=["cs.CE", "physics.flu-dyn", "math.OC"],
            start_to_close_timeout=timedelta(minutes=10)
        )

        # Score and gate
        for paper in new_papers:
            ku = await workflow.execute_activity(extract_knowledge_unit, paper)
            quality = await workflow.execute_activity(evaluate_knowledge_unit, ku)
            if quality.score >= 0.8:
                await workflow.execute_activity(store_to_vault, ku)
```

### Nightly Memory Consolidation

```python
@workflow.defn
class NightlyConsolidationWorkflow:
    @workflow.run
    async def run(self) -> None:
        # Replay last 7 days of episodes
        # Consolidate episodic → semantic
        # FSRS-6 utility scoring + prune
        # Reinforce high-utility memories
        ...
```

---

## Human-in-the-Loop Gates

Gates that **pause the workflow** and wait for human approval:

| Trigger | Pause Duration | Action Required |
|---|---|---|
| `confidence < 0.7` | Up to 24h | Review findings, approve or reject |
| `vault contradiction detected` | Up to 48h | Resolve contradiction, choose correct version |
| `Tier 1 constitution violation` | Up to 24h | Review violation, determine root cause |
| `all providers unavailable > 1h` | Up to 72h | Provision alternative provider |
| `quality_score < 0.5` (severe) | Up to 24h | Review for systemic prompt issue |

Notifications sent via Uptime Kuma push → Discord/Telegram when pause is triggered.

---

## Two-Timescale Learning

| Timescale | Loop | Frequency |
|---|---|---|
| **Per-run** (minutes–hours) | Execute → Evaluate → Distill → Gate → Store | Every run |
| **Scheduled** (daily/weekly) | External discovery → Quality gate → Vault | Cron (Temporal) |
| **Nightly** | Memory consolidation → FSRS-6 scoring → Prune | Nightly cron |

---

## Learning Health Metrics

Track these over time to detect if FORGE is getting smarter or dumber:

| Metric | Healthy Trend | Warning Sign |
|---|---|---|
| `quality_score` distribution | Shifting right (improving) | Shifting left |
| `strategy_reuse_rate` | Increasing | Flat or decreasing |
| `novel_insight_rate` | Stable or growing | Declining (stagnating) |
| `token_efficiency` | Decreasing (fewer tokens/task) | Increasing |
| `vault_contradiction_rate` | Low and stable | Rising |
| `memory_utility_mean` | High and stable | Declining (memory bloat) |

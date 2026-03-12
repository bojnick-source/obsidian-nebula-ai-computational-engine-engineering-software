"""
forge_agent/core/multi_agent_orchestrator.py

MultiAgentOrchestrator — committee mode orchestration (v2).

Moved from forge_agent/agents/multi_agent_orchestrator.py — orchestration is
infrastructure, not a domain agent. It belongs in core/ alongside governance.py,
mcp_manager.py, token_budget.py, etc.

FIXES APPLIED (vs the original v1 orchestrator.py):

1. _parse_assignments()       — structured XML output contract, not json.loads() on free text
2. _find_independent_groups() — real dependency graph using topological sort (asyncio.gather
                                for independent groups)
3. Vault write persistence    — _pending_tasks list + drain in shutdown, never drop silently
"""

import re
import json
import asyncio
import hashlib
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ─── Disagreement escalation type (also used by governance.py) ────────────────

# Defined here so orchestrator can produce it; governance.py imports it.


class HumanEscalation:
    """
    Sentinel returned by _resolve_disagreement when the Math Synthesizer
    cannot resolve the conflict mathematically.  Signals that human review
    is required before the blackboard entry can be marked resolved.
    """

    def __init__(self, reason: str, disambiguating_experiment: str = ""):
        self.reason = reason
        self.disambiguating_experiment = disambiguating_experiment

    def to_dict(self) -> dict:
        return {
            "type": "human_escalation",
            "reason": self.reason,
            "disambiguating_experiment": self.disambiguating_experiment,
        }


# ─── Assignment schema ────────────────────────────────────────────────────────


@dataclass
class TaskAssignment:
    """A single specialist assignment produced by the Orchestrator."""

    id: str
    agent: str                                        # key in SPECIALISTS or MATHEMATICIANS
    subproblem: str                                   # natural language description
    depends_on: list[str] = field(default_factory=list)  # ids of prerequisite tasks
    priority: int = 0                                 # lower = run earlier within a group


# ─── FIX 1: Structured orchestrator output contract ───────────────────────────
#
# Problem: json.loads() on free LLM text fails silently — any hallucination
# routes the entire problem to a single ME via the fallback.
#
# Fix: Force the Orchestrator to produce XML-tagged structured output.
# XML is more robust than JSON for LLM output because:
#   - LLMs reliably close XML tags even under pressure
#   - Partial responses are recoverable (unlike truncated JSON)
#   - No escaping edge cases for nested content
#
# The Orchestrator's system prompt includes this contract verbatim.

ORCHESTRATOR_ASSIGNMENT_SCHEMA = """
You MUST respond with a task decomposition in this exact XML format.
No prose before the opening <assignments> tag. No prose after </assignments>.

<assignments>
  <task id="t001" agent="ME" depends_on="">
    Derive the rotor blade chord length using momentum theory.
    Given: payload mass, disk loading, rotor count.
    Required: chord c [m], solidity σ [-].
  </task>
  <task id="t002" agent="Controls" depends_on="t001">
    Design collective pitch control law given chord and RPM from t001.
  </task>
  <task id="t003" agent="Materials" depends_on="">
    Select blade material for 10^7 cycle fatigue life at operating stress.
    Independent of t001 — can run in parallel.
  </task>
</assignments>

Rules:
- id: unique string, short (t001, t002, …)
- agent: one of ME / EE / SE / Controls / Thermal / Materials / Manufacturing /
  Safety / Acoustics / NumericalMethods / Plasma /
  Math_Symbolic / Math_Optimization / Math_PDE /
  Math_NumericalAnalysis / Math_Geometry / Math_Probability
- depends_on: comma-separated list of prerequisite task ids, or empty string
- Body: the subproblem statement — be specific, include what is given and what
  is required
"""


def parse_assignments_from_xml(xml_text: str) -> list[TaskAssignment]:
    """
    FIX 1: Parse Orchestrator output from structured XML.

    Replaces the old json.loads() fallback that silently routed everything
    to a single ME on parse failure.

    Raises ValueError if the XML is malformed enough to be unrecoverable,
    so the caller can ask the Orchestrator to retry rather than silently
    degrading.
    """
    # Extract the <assignments> block — be permissive about surrounding text
    match = re.search(r"<assignments>(.*?)</assignments>", xml_text, re.DOTALL)
    if not match:
        raise ValueError(
            "Orchestrator response missing <assignments>...</assignments> block. "
            f"Raw response snippet: {xml_text[:500]!r}"
        )

    assignments_xml = match.group(1)

    # Parse individual <task> elements
    task_pattern = re.compile(
        r'<task\s+'
        r'id=["\'](?P<id>[^"\']+)["\']'
        r'\s+agent=["\'](?P<agent>[^"\']+)["\']'
        r'\s+depends_on=["\'](?P<depends_on>[^"\']*)["\']'
        r'\s*>(?P<body>.*?)</task>',
        re.DOTALL,
    )

    tasks = []
    for m in task_pattern.finditer(assignments_xml):
        raw_depends = m.group("depends_on").strip()
        depends_on = (
            [d.strip() for d in raw_depends.split(",") if d.strip()]
            if raw_depends else []
        )
        tasks.append(TaskAssignment(
            id=m.group("id").strip(),
            agent=m.group("agent").strip(),
            subproblem=m.group("body").strip(),
            depends_on=depends_on,
        ))

    if not tasks:
        raise ValueError(
            "Parsed <assignments> block but found no <task> elements. "
            f"Block content: {assignments_xml[:300]!r}"
        )

    return tasks


# ─── FIX 2: Real dependency graph with topological sort ───────────────────────
#
# Problem: _find_independent_groups() returned [[all_tasks]] (all serial).
# For 8 specialists this multiplies latency by 8x.
#
# Fix: Kahn's algorithm topological sort → groups of tasks that share the
# same "depth" in the DAG can run in parallel via asyncio.gather().


def find_independent_groups(
    assignments: list[TaskAssignment],
) -> list[list[TaskAssignment]]:
    """
    FIX 2: Topological sort of task dependency DAG.

    Returns a list of groups.  Tasks within the same group have no mutual
    dependencies and can be executed in parallel (asyncio.gather).
    Groups are ordered so earlier groups complete before later groups start.

    Raises ValueError on cyclic dependencies.
    """
    # Build id → task map
    task_map: dict[str, TaskAssignment] = {t.id: t for t in assignments}

    # In-degree count and adjacency list
    in_degree: dict[str, int] = {t.id: 0 for t in assignments}
    dependents: dict[str, list[str]] = {t.id: [] for t in assignments}

    for task in assignments:
        for dep_id in task.depends_on:
            if dep_id not in task_map:
                logger.warning(
                    "Task %s depends on unknown task %s — treating as no dependency",
                    task.id, dep_id,
                )
                continue
            in_degree[task.id] += 1
            dependents[dep_id].append(task.id)

    # Kahn's algorithm
    groups: list[list[TaskAssignment]] = []
    current_wave = [t for t in assignments if in_degree[t.id] == 0]

    while current_wave:
        current_wave.sort(key=lambda t: t.priority)
        groups.append(current_wave)

        next_wave: list[TaskAssignment] = []
        for task in current_wave:
            for dep_id in dependents[task.id]:
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    next_wave.append(task_map[dep_id])
        current_wave = next_wave

    # Cycle detection
    remaining = [t for t in assignments if in_degree[t.id] > 0]
    if remaining:
        cycle_ids = [t.id for t in remaining]
        raise ValueError(
            f"Cyclic dependency detected among tasks: {cycle_ids}. "
            "Orchestrator produced an invalid dependency graph."
        )

    return groups


# ─── FIX 3: Vault write persistence ───────────────────────────────────────────
#
# Problem: asyncio.create_task(…) without storing a reference means Python's
# garbage collector can destroy the coroutine before it completes on fast runs.
# Vault writes silently dropped.
#
# Fix: _pending_tasks list on the orchestrator.  All vault-write tasks are
# appended here.  GracefulShutdown calls drain_pending_tasks() before exit.


class MultiAgentOrchestrator:
    """
    Routes subproblems to specialist agents, merges via blackboard.

    All three fixes integrated:
      - Structured XML output parsing (no json.loads fragility)
      - Parallel execution for independent task groups
      - Persistent task references (no silent vault write drops)
    """

    def __init__(self, model_router, vault):
        self.model_router = model_router
        self.vault = vault

        # FIX 3: Explicit task registry — never use bare create_task() without appending here
        self._pending_tasks: list[asyncio.Task] = []

        self.blackboard = None
        self.max_verification_rounds = 3

    # ── Public API ─────────────────────────────────────────────────────────────

    async def solve(
        self,
        problem: str,
        context: str = "",
        project_path: str | None = None,
    ) -> dict:
        """
        Full multi-agent solve with blackboard, verification, and vault persistence.

        Flow:
          1. Librarian retrieves vault context
          2. Orchestrator decomposes → structured XML → parsed TaskAssignment list
          3. Dependency graph computed → independent groups run in parallel
          4. Math Synthesizer unifies formulations
          5. Verifier gates (up to 3 rounds)
          6. Disagreements resolved (or escalated to human)
          7. Final merge
          8. Vault write-back (non-blocking, reference held)
        """
        from forge_agent.memory.blackboard import Blackboard

        self.blackboard = Blackboard(
            problem_id=hashlib.md5(problem.encode()).hexdigest()[:12],
            problem_statement=problem,
        )

        # ── Step 1: Library retrieval ──────────────────────────────────────────
        vault_context = await self._call_agent(
            "Librarian",
            f"Search the vault for knowledge relevant to this problem.\n\n"
            f"Problem: {problem}\nProject: {project_path or 'none'}",
        )

        # ── Step 2: Orchestrator decomposes → structured XML ───────────────────
        raw_decomposition = await self._call_agent(
            "Orchestrator",
            f"Decompose this problem and assign tasks.\n\n"
            f"Problem: {problem}\n\n"
            f"Vault context:\n{vault_context}\n\n"
            f"Current context:\n{context}\n\n"
            f"{ORCHESTRATOR_ASSIGNMENT_SCHEMA}",
        )

        # FIX 1: Structured XML parse with retry on failure
        assignments = await self._parse_assignments_with_retry(
            raw_decomposition, problem, context, vault_context
        )

        # ── Step 3: Parallel execution via dependency graph ────────────────────
        # FIX 2: Real topological sort → asyncio.gather() within groups
        try:
            groups = find_independent_groups(assignments)
        except ValueError as e:
            logger.error("Dependency graph error: %s — falling back to serial", e)
            groups = [[a] for a in assignments]  # safe fallback: all serial

        specialist_results: dict[str, str] = {}

        for group in groups:
            group_coroutines = [
                self._call_specialist(
                    assignment.agent,
                    assignment.subproblem,
                    self.blackboard.get_context_for_agent(assignment.agent),
                )
                for assignment in group
            ]

            group_outputs = await asyncio.gather(*group_coroutines)

            for assignment, result in zip(group, group_outputs):
                specialist_results[assignment.id] = result
                self._integrate_specialist_result(assignment.id, result)

            logger.info(
                "Completed group of %d task(s): %s",
                len(group), [a.id for a in group],
            )

        # ── Step 4: Math Synthesizer ───────────────────────────────────────────
        if len(specialist_results) > 1:
            synthesis = await self._call_agent(
                "MathSynthesizer",
                f"Unify formulations from {len(specialist_results)} specialists.\n\n"
                f"Blackboard:\n{self.blackboard.get_context_for_agent('MathSynthesizer')}",
            )
            self._integrate_synthesis(synthesis)

        # ── Step 5: Verification loop ──────────────────────────────────────────
        verification_round = 0
        for verification_round in range(self.max_verification_rounds):
            verdict = await self._call_agent(
                "Verifier",
                f"Verify all work on the blackboard.\n\n"
                f"Blackboard:\n{self.blackboard.get_context_for_agent('Verifier')}",
            )
            parsed_verdict = self._parse_verdict(verdict)

            if parsed_verdict["verdict"] == "PASS":
                self.blackboard.confidence = parsed_verdict.get("confidence", 0.9)
                break

            for violation in parsed_verdict.get("violations", []):
                responsible = violation.get("responsible_agent")
                if responsible:
                    revision = await self._call_specialist(
                        responsible,
                        f"VERIFIER REJECTED your work.\n"
                        f"Fix this: {violation['description']}\n\n"
                        f"Blackboard:\n"
                        f"{self.blackboard.get_context_for_agent(responsible)}",
                        self.blackboard.get_context_for_agent(responsible),
                    )
                    self._integrate_specialist_result(
                        violation.get("assignment_id", "revision"), revision
                    )

        # ── Step 6: Disagreement resolution ───────────────────────────────────
        for disagreement in self.blackboard.disagreements:
            if disagreement["resolution"] is None:
                resolution = await self._resolve_disagreement(disagreement)

                if isinstance(resolution, HumanEscalation):
                    disagreement["resolution"] = None
                    disagreement["escalation"] = resolution.to_dict()
                    logger.warning(
                        "Disagreement %s escalated: %s",
                        disagreement["id"], resolution.reason,
                    )
                else:
                    disagreement["resolution"] = resolution

        # ── Step 7: Final merge ────────────────────────────────────────────────
        final = await self._call_agent(
            "Orchestrator",
            f"Produce the final merged response.\n\n"
            f"Blackboard:\n{self.blackboard.get_context_for_agent('Orchestrator')}",
        )

        # ── Step 8: Vault write-back ───────────────────────────────────────────
        # FIX 3: Store the task reference — never drop silently
        vault_task = asyncio.create_task(
            self._persist_to_vault(project_path)
        )
        self._pending_tasks.append(vault_task)

        # Clean up completed tasks opportunistically
        self._pending_tasks = [t for t in self._pending_tasks if not t.done()]

        return {
            "response": final,
            "blackboard": self.blackboard.to_dict(),
            "confidence": self.blackboard.confidence,
            "agents_involved": list(specialist_results.keys()),
            "verification_rounds": verification_round + 1,
            "disagreements": self.blackboard.disagreements,
        }

    async def drain_pending_tasks(self, timeout_s: float = 30.0) -> None:
        """
        FIX 3: Await all pending vault write tasks before shutdown.

        Called by GracefulShutdown.  Waits up to timeout_s seconds.
        Any tasks that don't complete are logged as warnings.
        """
        if not self._pending_tasks:
            return

        active = [t for t in self._pending_tasks if not t.done()]
        if not active:
            self._pending_tasks.clear()
            return

        logger.info(
            "Draining %d pending vault write tasks (timeout: %ss)",
            len(active), timeout_s,
        )

        done, pending = await asyncio.wait(active, timeout=timeout_s)

        for task in done:
            if task.exception():
                logger.error("Vault write task failed: %s", task.exception())

        for task in pending:
            logger.warning(
                "Vault write task did not complete within timeout — cancelling"
            )
            task.cancel()

        self._pending_tasks.clear()

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _parse_assignments_with_retry(
        self,
        raw: str,
        problem: str,
        context: str,
        vault_context: str,
        max_retries: int = 2,
    ) -> list[TaskAssignment]:
        """
        FIX 1: Parse structured XML; retry Orchestrator call on parse failure.
        Never silently falls back to single-agent routing.
        """
        for attempt in range(max_retries + 1):
            try:
                return parse_assignments_from_xml(raw)
            except ValueError as e:
                if attempt == max_retries:
                    logger.error(
                        "Orchestrator failed to produce valid XML after %d attempts. "
                        "Raising to caller — do not silently degrade.",
                        max_retries + 1,
                    )
                    raise RuntimeError(
                        f"Orchestrator XML parse failed after {max_retries + 1} attempts: {e}"
                    ) from e

                logger.warning(
                    "Attempt %d: Orchestrator XML parse failed (%s). Retrying.",
                    attempt + 1, e,
                )
                raw = await self._call_agent(
                    "Orchestrator",
                    f"Your previous response was rejected because: {e}\n\n"
                    f"Try again. Follow the XML schema EXACTLY.\n\n"
                    f"{ORCHESTRATOR_ASSIGNMENT_SCHEMA}\n\n"
                    f"Problem: {problem}",
                )

        raise RuntimeError("Should not reach here")  # satisfies type checker

    async def _resolve_disagreement(
        self, disagreement: dict
    ) -> "str | HumanEscalation":
        """
        Disagreement resolution with escalation path.

        Returns:
            str             — resolution text (Math Synthesizer resolved it)
            HumanEscalation — when Math Synthesizer cannot resolve mathematically
        """
        resolution_text = await self._call_agent(
            "MathSynthesizer",
            f"Two agents disagree:\n"
            f"- {disagreement['agents'][0]}: {disagreement['position_a']}\n"
            f"- {disagreement['agents'][1]}: {disagreement['position_b']}\n\n"
            f"Topic: {disagreement['topic']}\n\n"
            f"REQUIRED OUTPUT FORMAT:\n"
            f"<resolution_verdict>RESOLVED | REQUIRES_HUMAN</resolution_verdict>\n"
            f"<resolution_text>your resolution or explanation</resolution_text>\n"
            f"<disambiguating_experiment>"
            f"specific test that would resolve if unresolved"
            f"</disambiguating_experiment>",
        )

        verdict_match = re.search(
            r"<resolution_verdict>(.*?)</resolution_verdict>",
            resolution_text, re.DOTALL,
        )
        text_match = re.search(
            r"<resolution_text>(.*?)</resolution_text>",
            resolution_text, re.DOTALL,
        )
        exp_match = re.search(
            r"<disambiguating_experiment>(.*?)</disambiguating_experiment>",
            resolution_text, re.DOTALL,
        )

        verdict = verdict_match.group(1).strip() if verdict_match else "REQUIRES_HUMAN"
        text = text_match.group(1).strip() if text_match else resolution_text
        experiment = exp_match.group(1).strip() if exp_match else ""

        if verdict == "RESOLVED":
            return text
        return HumanEscalation(reason=text, disambiguating_experiment=experiment)

    async def _persist_to_vault(self, project_path: str | None) -> None:
        """Write blackboard results to Obsidian vault after a solve run."""
        try:
            note_path = (
                f"projects/{project_path or 'scratch'}"
                f"/blackboard_{self.blackboard.problem_id}.md"
            )

            has_unresolved = any(
                d.get("escalation") is not None
                for d in self.blackboard.disagreements
            )

            self.vault.upsert_note(
                path=note_path,
                markdown=self.blackboard.to_obsidian_note(),
                frontmatter={
                    "type": "blackboard",
                    "confidence": self.blackboard.confidence,
                    "status": "requires-human-review" if has_unresolved else "draft",
                    "has_unresolved_disagreements": has_unresolved,
                },
            )

            if has_unresolved:
                escalated = [
                    d for d in self.blackboard.disagreements
                    if d.get("escalation") is not None
                ]
                self.vault.append_to_note(
                    note_path,
                    "\n\n## Requires Human Review\n\n"
                    + "\n".join(
                        f"- **{d['topic']}**: {d['escalation']['reason']}\n"
                        f"  - Disambiguate via: "
                        f"{d['escalation'].get('disambiguating_experiment', 'TBD')}"
                        for d in escalated
                    ),
                )

            logger.info("Vault write complete: %s", note_path)

        except Exception as e:
            logger.error(
                "Vault write failed for problem %s: %s",
                self.blackboard.problem_id, e,
            )
            raise  # Re-raise so drain_pending_tasks() can log it properly

    async def _call_agent(self, agent_key: str, prompt: str) -> str:
        """Call a named agent through the model router."""
        raise NotImplementedError("Implement with actual model_router.call()")

    async def _call_specialist(
        self, agent_key: str, subproblem: str, blackboard_context: str
    ) -> str:
        """Call a specialist with the current blackboard context."""
        raise NotImplementedError("Implement with actual model_router.call()")

    def _integrate_specialist_result(self, assign_id: str, result: str) -> None:
        """Parse specialist output and write structured fields to blackboard."""
        raise NotImplementedError("Implement with blackboard.add_entry()")

    def _integrate_synthesis(self, synthesis: str) -> None:
        """Integrate Math Synthesizer output into blackboard."""
        self._integrate_specialist_result("MathSynthesizer", synthesis)

    def _parse_verdict(self, verdict: str) -> dict:
        """Parse Verifier output — JSON first, keyword fallback."""
        try:
            return json.loads(verdict)
        except json.JSONDecodeError:
            pass
        if "PASS" in verdict.upper():
            return {"verdict": "PASS", "confidence": 0.7}
        return {
            "verdict": "REJECT",
            "violations": [{"description": verdict, "responsible_agent": None}],
        }

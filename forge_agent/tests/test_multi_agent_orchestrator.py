"""
Tests for multi_agent_orchestrator.py — covers all three fixes:
  FIX 1: parse_assignments_from_xml
  FIX 2: find_independent_groups (topological sort + parallelism)
  FIX 3: drain_pending_tasks / _pending_tasks reference holding
"""

import asyncio
import pytest

from forge_agent.agents.multi_agent_orchestrator import (
    HumanEscalation,
    MultiAgentOrchestrator,
    TaskAssignment,
    find_independent_groups,
    parse_assignments_from_xml,
)


# ─── FIX 1: XML parsing ────────────────────────────────────────────────────────


VALID_XML = """
Some preamble the model might add.
<assignments>
  <task id="t001" agent="ME" depends_on="">
    Derive chord length from momentum theory.
  </task>
  <task id="t002" agent="Controls" depends_on="t001">
    Design pitch law using chord from t001.
  </task>
  <task id="t003" agent="Materials" depends_on="">
    Select blade material for fatigue life.
  </task>
</assignments>
Trailing prose is also ignored.
"""


class TestParseAssignmentsFromXml:
    def test_parses_three_tasks(self):
        tasks = parse_assignments_from_xml(VALID_XML)
        assert len(tasks) == 3

    def test_task_ids(self):
        tasks = parse_assignments_from_xml(VALID_XML)
        ids = [t.id for t in tasks]
        assert ids == ["t001", "t002", "t003"]

    def test_agent_names(self):
        tasks = parse_assignments_from_xml(VALID_XML)
        assert tasks[0].agent == "ME"
        assert tasks[1].agent == "Controls"
        assert tasks[2].agent == "Materials"

    def test_empty_depends_on_is_empty_list(self):
        tasks = parse_assignments_from_xml(VALID_XML)
        assert tasks[0].depends_on == []
        assert tasks[2].depends_on == []

    def test_populated_depends_on(self):
        tasks = parse_assignments_from_xml(VALID_XML)
        assert tasks[1].depends_on == ["t001"]

    def test_multi_depends_on(self):
        xml = """
        <assignments>
          <task id="t001" agent="ME" depends_on="">body</task>
          <task id="t002" agent="EE" depends_on="">body</task>
          <task id="t003" agent="Safety" depends_on="t001, t002">body</task>
        </assignments>
        """
        tasks = parse_assignments_from_xml(xml)
        assert tasks[2].depends_on == ["t001", "t002"]

    def test_raises_on_missing_assignments_block(self):
        with pytest.raises(ValueError, match="missing <assignments>"):
            parse_assignments_from_xml("No XML here, just prose.")

    def test_raises_on_empty_assignments_block(self):
        with pytest.raises(ValueError, match="no <task> elements"):
            parse_assignments_from_xml("<assignments>   </assignments>")

    def test_subproblem_body_stripped(self):
        tasks = parse_assignments_from_xml(VALID_XML)
        assert tasks[0].subproblem == "Derive chord length from momentum theory."


# ─── FIX 2: Topological sort ──────────────────────────────────────────────────


def _make_tasks(*specs) -> list[TaskAssignment]:
    """Helper: specs are (id, agent, depends_on_list)."""
    return [
        TaskAssignment(id=id_, agent=agent, subproblem="stub", depends_on=deps)
        for id_, agent, deps in specs
    ]


class TestFindIndependentGroups:
    def test_all_independent_one_group(self):
        tasks = _make_tasks(
            ("t001", "ME", []),
            ("t002", "EE", []),
            ("t003", "Materials", []),
        )
        groups = find_independent_groups(tasks)
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_linear_chain_three_groups(self):
        tasks = _make_tasks(
            ("t001", "ME", []),
            ("t002", "Controls", ["t001"]),
            ("t003", "Safety", ["t002"]),
        )
        groups = find_independent_groups(tasks)
        assert len(groups) == 3
        assert groups[0][0].id == "t001"
        assert groups[1][0].id == "t002"
        assert groups[2][0].id == "t003"

    def test_mixed_parallel_and_serial(self):
        # t001 and t003 are independent (depth 0)
        # t002 depends on t001 (depth 1)
        tasks = _make_tasks(
            ("t001", "ME", []),
            ("t002", "Controls", ["t001"]),
            ("t003", "Materials", []),
        )
        groups = find_independent_groups(tasks)
        assert len(groups) == 2
        group0_ids = {t.id for t in groups[0]}
        assert group0_ids == {"t001", "t003"}
        assert groups[1][0].id == "t002"

    def test_cycle_raises_value_error(self):
        tasks = _make_tasks(
            ("t001", "ME", ["t002"]),
            ("t002", "EE", ["t001"]),  # cycle
        )
        with pytest.raises(ValueError, match="Cyclic dependency"):
            find_independent_groups(tasks)

    def test_unknown_dependency_warning_no_crash(self):
        tasks = _make_tasks(
            ("t001", "ME", ["t999"]),  # t999 doesn't exist
        )
        # Should not raise — logs warning, treats as no dependency
        groups = find_independent_groups(tasks)
        assert len(groups) == 1

    def test_empty_assignments_returns_empty(self):
        groups = find_independent_groups([])
        assert groups == []

    def test_single_task_one_group(self):
        tasks = _make_tasks(("t001", "ME", []))
        groups = find_independent_groups(tasks)
        assert len(groups) == 1
        assert groups[0][0].id == "t001"

    def test_wide_diamond(self):
        # t001 → {t002, t003, t004} → t005
        tasks = _make_tasks(
            ("t001", "ME", []),
            ("t002", "EE", ["t001"]),
            ("t003", "Materials", ["t001"]),
            ("t004", "Thermal", ["t001"]),
            ("t005", "Safety", ["t002", "t003", "t004"]),
        )
        groups = find_independent_groups(tasks)
        assert len(groups) == 3
        assert len(groups[1]) == 3   # t002, t003, t004 all parallel
        assert groups[2][0].id == "t005"


# ─── FIX 3: Vault write persistence ───────────────────────────────────────────


class _StubOrchestrator(MultiAgentOrchestrator):
    """Minimal subclass that doesn't need real model_router or vault."""

    def __init__(self):
        # Bypass __init__ — we set attributes manually
        self._pending_tasks: list[asyncio.Task] = []
        self.blackboard = None
        self.max_verification_rounds = 3
        self.model_router = None
        self.vault = None


class TestDrainPendingTasks:
    @pytest.mark.asyncio
    async def test_drain_completes_fast_tasks(self):
        orch = _StubOrchestrator()

        completed = []

        async def fast_write():
            await asyncio.sleep(0.01)
            completed.append(1)

        task = asyncio.create_task(fast_write())
        orch._pending_tasks.append(task)

        await orch.drain_pending_tasks(timeout_s=5.0)
        assert len(completed) == 1
        assert orch._pending_tasks == []

    @pytest.mark.asyncio
    async def test_drain_cancels_slow_tasks(self):
        orch = _StubOrchestrator()

        async def slow_write():
            await asyncio.sleep(999)

        task = asyncio.create_task(slow_write())
        orch._pending_tasks.append(task)

        await orch.drain_pending_tasks(timeout_s=0.05)
        await asyncio.sleep(0)   # let the CancelledError propagate
        assert task.cancelled()
        assert orch._pending_tasks == []

    @pytest.mark.asyncio
    async def test_drain_noop_when_no_tasks(self):
        orch = _StubOrchestrator()
        # Should complete immediately without error
        await orch.drain_pending_tasks(timeout_s=1.0)

    @pytest.mark.asyncio
    async def test_completed_tasks_excluded_from_drain(self):
        orch = _StubOrchestrator()

        async def instant():
            pass

        task = asyncio.create_task(instant())
        await asyncio.sleep(0)  # let it complete
        orch._pending_tasks.append(task)
        assert task.done()

        await orch.drain_pending_tasks(timeout_s=1.0)
        assert orch._pending_tasks == []

    @pytest.mark.asyncio
    async def test_multiple_tasks_all_drained(self):
        orch = _StubOrchestrator()
        results = []

        async def write(n):
            await asyncio.sleep(0.01)
            results.append(n)

        for i in range(5):
            task = asyncio.create_task(write(i))
            orch._pending_tasks.append(task)

        await orch.drain_pending_tasks(timeout_s=5.0)
        assert sorted(results) == [0, 1, 2, 3, 4]
        assert orch._pending_tasks == []


# ─── HumanEscalation ──────────────────────────────────────────────────────────


class TestHumanEscalation:
    def test_to_dict_contains_required_keys(self):
        esc = HumanEscalation(
            reason="Conflicting yield strength values",
            disambiguating_experiment="Perform tensile test per ASTM E8",
        )
        d = esc.to_dict()
        assert d["type"] == "human_escalation"
        assert "Conflicting" in d["reason"]
        assert "ASTM E8" in d["disambiguating_experiment"]

    def test_to_dict_empty_experiment(self):
        esc = HumanEscalation(reason="Cannot resolve")
        d = esc.to_dict()
        assert d["disambiguating_experiment"] == ""

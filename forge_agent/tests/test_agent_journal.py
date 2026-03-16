"""Unit tests for AgentJournal — four-W operation journaling."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import pytest

from forge_agent.memory.agent_journal import (
    AgentJournal,
    JournalEntry,
    _atomic_write,
    _render_note,
    _slug,
)


# ------------------------------------------------------------------ fixtures


@pytest.fixture()
def trace_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture()
def journal(trace_id: str) -> AgentJournal:
    """Journal with no vault (vault=None) — tests in-memory behaviour only."""
    return AgentJournal(
        vault_manager=None,
        agent_id="test_agent",
        trace_id=trace_id,
    )


# ------------------------------------------------------------------ four-W recording


class TestOperationContextManager:
    def test_success_records_entry(self, journal: AgentJournal) -> None:
        with journal.operation(
            "compute_drag",
            why="user requested drag estimate for Aladdin-3B fin",
            how="Prandtl lifting-line, AR=4.2",
        ):
            pass

        assert len(journal.entries()) == 1
        e = journal.last_entry()
        assert e is not None
        assert e.what == "compute_drag"
        assert e.why == "user requested drag estimate for Aladdin-3B fin"
        assert e.how == "Prandtl lifting-line, AR=4.2"
        assert e.outcome == "success"
        assert e.duration_ms >= 0.0
        assert e.when != ""

    def test_four_w_all_populated(self, journal: AgentJournal) -> None:
        with journal.operation(
            "ingest_notebooklm_export",
            why="new PDF landed in inbox/",
            how="parse frontmatter → extract claims → cross-check vault",
            domain="cross_domain",
        ) as op:
            op.state_before = {"inbox_count": 3}
            op.state_after = {"inbox_count": 2, "new_note": "engineering/materials/al7075.md"}
            op.notes = "Claim verified against ISA standard"

        e = journal.last_entry()
        assert e.what == "ingest_notebooklm_export"
        assert e.why == "new PDF landed in inbox/"
        assert e.how == "parse frontmatter → extract claims → cross-check vault"
        assert e.state_before == {"inbox_count": 3}
        assert e.state_after["new_note"] == "engineering/materials/al7075.md"
        assert "ISA standard" in e.notes
        assert e.domain == "cross_domain"

    def test_failure_records_error_and_re_raises(self, journal: AgentJournal) -> None:
        with pytest.raises(ValueError, match="solver did not converge"):
            with journal.operation(
                "run_fea",
                why="topology_optimization handoff",
                how="iterative FEA, Δ=0.1mm",
            ):
                raise ValueError("solver did not converge")

        e = journal.last_entry()
        assert e is not None
        assert e.outcome == "failure"
        assert e.error == "solver did not converge"
        assert e.duration_ms >= 0.0

    def test_sequence_is_monotonic(self, journal: AgentJournal) -> None:
        for i in range(5):
            with journal.operation(f"op_{i}", why="test", how="direct"):
                pass

        seqs = [e.op_sequence for e in journal.entries()]
        assert seqs == list(range(1, 6))

    def test_timestamp_is_iso8601(self, journal: AgentJournal) -> None:
        with journal.operation("ts_test", why="check timestamp format", how="noop"):
            pass
        e = journal.last_entry()
        assert e is not None
        # Basic ISO 8601 UTC check: ends with +00:00 or Z
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", e.when)


# ------------------------------------------------------------------ causality chain


class TestCausalityChain:
    def test_root_op_has_no_triggered_by(self, journal: AgentJournal) -> None:
        with journal.operation("root_op", why="initial trigger", how="direct"):
            pass
        e = journal.last_entry()
        assert e is not None
        assert e.triggered_by is None

    def test_child_links_to_parent(self, journal: AgentJournal) -> None:
        with journal.operation("parent_op", why="root cause", how="noop") as parent:
            parent_id = parent.id

        with journal.operation(
            "child_op",
            why="because parent_op triggered a need",
            how="follow-up call",
            parent_op_id=parent_id,
        ):
            pass

        child = journal.last_entry()
        assert child is not None
        assert child.triggered_by == parent_id

    def test_causality_chain_traversal(self, journal: AgentJournal) -> None:
        with journal.operation("root", why="initial", how="noop") as r:
            root_id = r.id
        with journal.operation("middle", why="from root", how="noop", parent_op_id=root_id) as m:
            mid_id = m.id
        with journal.operation("leaf", why="from middle", how="noop", parent_op_id=mid_id) as lf:
            leaf_id = lf.id

        chain = journal.causality_chain(leaf_id)
        assert len(chain) == 3
        assert chain[0].what == "root"
        assert chain[1].what == "middle"
        assert chain[2].what == "leaf"

    def test_causality_chain_for_root_returns_single(self, journal: AgentJournal) -> None:
        with journal.operation("only_op", why="standalone", how="noop") as op:
            op_id = op.id
        chain = journal.causality_chain(op_id)
        assert len(chain) == 1
        assert chain[0].what == "only_op"


# ------------------------------------------------------------------ direct record()


class TestDirectRecord:
    def test_direct_record_assigns_seq(self, journal: AgentJournal) -> None:
        entry = JournalEntry(what="manual_op", why="direct test", how="unit test")
        journal.record(entry)
        assert entry.op_sequence == 1

    def test_direct_record_populates_agent_fields(self, journal: AgentJournal) -> None:
        entry = JournalEntry(what="op", why="w", how="h")
        journal.record(entry)
        assert entry.agent_id == "test_agent"
        assert entry.agent_version == "1.0.0"
        assert entry.trace_id == journal.trace_id

    def test_direct_record_does_not_overwrite_existing_fields(
        self, journal: AgentJournal
    ) -> None:
        custom_id = str(uuid.uuid4())
        entry = JournalEntry(
            id=custom_id,
            agent_id="override_agent",
            what="op",
            why="w",
            how="h",
            op_sequence=99,
        )
        journal.record(entry)
        assert entry.id == custom_id
        assert entry.agent_id == "override_agent"
        assert entry.op_sequence == 99


# ------------------------------------------------------------------ summary()


class TestSummary:
    def test_summary_counts_correctly(self, journal: AgentJournal) -> None:
        with journal.operation("s1", why="test", how="noop"):
            pass
        with journal.operation("s2", why="test", how="noop"):
            pass
        with pytest.raises(RuntimeError):
            with journal.operation("s3", why="test", how="noop"):
                raise RuntimeError("boom")

        s = journal.summary()
        assert s["total_ops"] == 3
        assert s["success"] == 2
        assert s["failure"] == 1
        assert s["total_duration_ms"] >= 0.0
        assert s["agent_id"] == "test_agent"

    def test_empty_summary(self, journal: AgentJournal) -> None:
        s = journal.summary()
        assert s["total_ops"] == 0
        assert s["success"] == 0


# ------------------------------------------------------------------ vault writes


class TestVaultWrites:
    def test_atomic_write_creates_file(self, tmp_path: Path) -> None:
        target = tmp_path / "test_note.md"
        _atomic_write(target, "# Hello\ncontent")
        assert target.exists()
        assert target.read_text() == "# Hello\ncontent"

    def test_atomic_write_no_tmp_left_behind(self, tmp_path: Path) -> None:
        target = tmp_path / "test_note.md"
        _atomic_write(target, "content")
        tmp = target.with_suffix(".tmp")
        assert not tmp.exists()

    def test_journal_with_real_vault(self, tmp_path: Path) -> None:
        """End-to-end: journal writes file to vault directory."""
        from forge_agent.memory.obsidian_manager import ObsidianVaultManager

        vault_mgr = ObsidianVaultManager(vault_path=tmp_path / "vault")
        vault_mgr._ensure_indexed_sync()  # init sync index

        journal = AgentJournal(
            vault_manager=vault_mgr,
            agent_id="librarian",
            trace_id=str(uuid.uuid4()),
        )

        with journal.operation(
            "write_finding",
            why="verifier returned confidence=0.91",
            how="upsert_note to engineering/constraints/",
        ) as op:
            op.state_before = {"draft": "Al7075_fatigue_limit_v0"}
            op.state_after = {"written": "engineering/constraints/al7075_fatigue.md"}

        # File must exist in vault
        trace_dir = vault_mgr.vault_path / "engineering" / "agent-thinking"
        notes = list(trace_dir.rglob("*.md"))
        assert len(notes) == 1

        content = notes[0].read_text()
        assert "write_finding" in content
        assert "WHY" in content
        assert "HOW" in content
        assert "State Before" in content
        assert "State After" in content

    def test_journal_none_vault_does_not_raise(self, journal: AgentJournal) -> None:
        result = journal.record(JournalEntry(what="op", why="w", how="h"))
        assert result is None


# ------------------------------------------------------------------ render_note()


class TestRenderNote:
    def test_render_contains_all_four_ws(self) -> None:
        entry = JournalEntry(
            what="solve_plasma",
            why="physics team request",
            how="MHD solver, Bz=2T",
            when="2026-03-16T12:00:00+00:00",
            outcome="success",
            duration_ms=123.4,
        )
        md = _render_note(entry)
        assert "## WHAT" in md
        assert "## WHY" in md
        assert "## HOW" in md
        assert "solve_plasma" in md
        assert "physics team request" in md
        assert "MHD solver, Bz=2T" in md

    def test_render_shows_root_op_when_no_parent(self) -> None:
        entry = JournalEntry(what="root", why="w", how="h", triggered_by=None)
        md = _render_note(entry)
        assert "root operation" in md

    def test_render_shows_causality_link_when_has_parent(self) -> None:
        parent_id = str(uuid.uuid4())
        entry = JournalEntry(what="child", why="w", how="h", triggered_by=parent_id)
        md = _render_note(entry)
        assert parent_id in md

    def test_render_failure_includes_error_section(self) -> None:
        entry = JournalEntry(
            what="failing_op",
            why="w",
            how="h",
            outcome="failure",
            error="division by zero",
        )
        md = _render_note(entry)
        assert "## Error" in md
        assert "division by zero" in md

    def test_render_annotations_section_present_when_notes_given(self) -> None:
        entry = JournalEntry(what="op", why="w", how="h", notes="key insight here")
        md = _render_note(entry)
        assert "## Annotations" in md
        assert "key insight here" in md

    def test_render_no_annotations_section_when_empty_notes(self) -> None:
        entry = JournalEntry(what="op", why="w", how="h", notes="")
        md = _render_note(entry)
        assert "## Annotations" not in md


# ------------------------------------------------------------------ slug helper


def test_slug_strips_special_chars() -> None:
    # hyphens are kept (valid in filenames); spaces, parens, dots are replaced with _
    assert _slug("Solve Heat-Exchanger (v2)") == "solve_heat-exchanger__v2_"


def test_slug_truncates_at_48() -> None:
    long = "a" * 100
    assert len(_slug(long)) <= 48

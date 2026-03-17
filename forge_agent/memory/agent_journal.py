"""
AgentJournal — four-W operation journaling for FORGE agents.

Inspired by the causally-linked, crash-safe activity logging observed in
sophisticated self-documenting systems: every operation records WHAT was
done, WHEN it happened, HOW it was done (method/API/algorithm), and WHY
it was triggered (goal/precondition/parent op). Entries are linked by
``triggered_by`` UUID forming an auditable causality chain.

Key properties
--------------
- Atomic writes: temp file → rename (POSIX rename is atomic; survives crash mid-write)
- Causality chain: each entry carries ``triggered_by`` referencing its parent UUID
- Monotonic sequence: ``op_sequence`` counter scoped per trace_id
- Vault persistence: entries land in ``engineering/agent-thinking/`` as Obsidian notes
- Lightweight: no async required; syncs directly via ObsidianVaultManager.upsert_note()

Usage
-----
    journal = AgentJournal(vault_manager, agent_id="librarian", trace_id=run_id)

    # Context-manager style (recommended)
    with journal.operation(
        "search_vault",
        why="user asked about Al 7075 fatigue limit",
        how="TF-IDF full-text search, top_k=10",
    ) as op:
        op.state_before = {"query": "Al 7075 fatigue", "vault_size": 312}
        results = vault.search_notes("Al 7075 fatigue")
        op.state_after = {"hits": len(results), "top_score": results[0].score}
        op.notes = "Found 3 relevant notes; top match confidence=0.87"

    # Direct record style (for pre-computed entries)
    entry = JournalEntry(what="topology_optimization_handoff", why="...", how="...")
    journal.record(entry)
"""

from __future__ import annotations

import os
import re
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from forge_agent.memory.obsidian_manager import ObsidianVaultManager


# ------------------------------------------------------------------ entry


@dataclass
class JournalEntry:
    """A single four-W operation record.

    All fields are mandatory except ``triggered_by`` (None for root ops)
    and the mutable payload fields (``state_before``, ``state_after``,
    ``notes``, ``tags``) which the caller fills inside the context manager.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    agent_version: str = "1.0.0"
    trace_id: str = ""           # run / session UUID
    triggered_by: str | None = None   # parent entry UUID (None = root op)
    op_sequence: int = 0         # monotonic counter scoped to trace_id

    # Four Ws
    what: str = ""               # WHAT: operation name + brief description
    why: str = ""                # WHY: goal / trigger / precondition
    how: str = ""                # HOW: method / API / algorithm used
    when: str = ""               # WHEN: ISO 8601 UTC timestamp (set at entry creation)

    # Domain
    domain: str = "cross_domain"

    # State deltas
    state_before: dict = field(default_factory=dict)
    state_after: dict = field(default_factory=dict)

    # Outcome
    outcome: str = "pending"     # pending | success | failure | partial
    duration_ms: float = 0.0
    error: str | None = None

    # Free-form annotations
    notes: str = ""              # markdown — decisions, alternatives, observations
    tags: list[str] = field(default_factory=list)


# ------------------------------------------------------------------ context


class _OperationContext:
    """Returned by ``AgentJournal.operation()``; caller mutates it inside ``with``."""

    def __init__(self, entry: JournalEntry) -> None:
        self._entry = entry

    # Expose JournalEntry fields directly so callers can write:
    #   op.state_before = {...}
    #   op.notes = "..."

    @property
    def id(self) -> str:
        return self._entry.id

    @property
    def state_before(self) -> dict:
        return self._entry.state_before

    @state_before.setter
    def state_before(self, value: dict) -> None:
        self._entry.state_before = value

    @property
    def state_after(self) -> dict:
        return self._entry.state_after

    @state_after.setter
    def state_after(self, value: dict) -> None:
        self._entry.state_after = value

    @property
    def notes(self) -> str:
        return self._entry.notes

    @notes.setter
    def notes(self, value: str) -> None:
        self._entry.notes = value

    @property
    def tags(self) -> list[str]:
        return self._entry.tags

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._entry.tags = value


# ------------------------------------------------------------------ journal


class AgentJournal:
    """Four-W operation journal — bridges AgentLogger (JSONL) and ObsidianVaultManager.

    Each call to ``operation()`` or ``record()`` atomically writes a vault note
    to ``engineering/agent-thinking/<trace_id>/`` and maintains a sequence counter.

    Parameters
    ----------
    vault_manager:
        Live ``ObsidianVaultManager`` instance (or None to disable vault writes —
        useful in tests that don't need a real vault).
    agent_id:
        Canonical agent identifier (e.g. ``"librarian"``, ``"verifier"``).
    trace_id:
        UUID of the current run/session; all entries for one run share this value.
    agent_version:
        Semver string written into every note's frontmatter.
    vault_subdir:
        Vault-relative directory for journal notes.
        Defaults to ``"engineering/agent-thinking"``.
    """

    def __init__(
        self,
        vault_manager: "ObsidianVaultManager | None",
        agent_id: str,
        trace_id: str,
        agent_version: str = "1.0.0",
        vault_subdir: str = "engineering/agent-thinking",
        task_id: str = "",
    ) -> None:
        self._vault = vault_manager
        self.agent_id = agent_id
        self.trace_id = trace_id
        self.task_id = task_id
        self.agent_version = agent_version
        self.vault_subdir = vault_subdir
        self._seq: int = 0                   # monotonic per-trace counter
        self._entries: list[JournalEntry] = []  # in-memory history for this session

    # ---------------------------------------------------------------- public

    @contextmanager
    def operation(
        self,
        what: str,
        *,
        why: str,
        how: str,
        domain: str = "cross_domain",
        parent_op_id: str | None = None,
    ) -> Generator[_OperationContext, None, None]:
        """Context manager that records a four-W entry on exit.

        The entry is written to the vault even if the operation raises —
        in that case ``outcome`` is set to ``"failure"`` and the exception
        message is captured in ``entry.error``.

        Example
        -------
            with journal.operation(
                "solve_heat_exchanger",
                why="thermal specialist request",
                how="HelixHeatX CEM solver, Δ=0.5mm voxel",
                domain="thermal_fluids",
            ) as op:
                op.state_before = {"inlet_temp_K": 900, "wall_material": "Inconel 718"}
                result = run_solver(...)
                op.state_after = {"outlet_temp_K": result.T_out, "eff": result.efficiency}
                op.notes = "Converged in 14 iterations; wall thickness checked ≥ 0.8 mm"
        """
        self._seq += 1
        entry = JournalEntry(
            agent_id=self.agent_id,
            agent_version=self.agent_version,
            trace_id=self.trace_id,
            triggered_by=parent_op_id,
            op_sequence=self._seq,
            what=what,
            why=why,
            how=how,
            when=datetime.now(timezone.utc).isoformat(),
            domain=domain,
        )
        ctx = _OperationContext(entry)
        t0 = time.perf_counter()
        try:
            yield ctx
            entry.outcome = "success"
        except Exception as exc:
            entry.outcome = "failure"
            entry.error = str(exc)
            raise
        finally:
            entry.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            self.record(entry)

    def record(self, entry: JournalEntry) -> Path | None:
        """Atomically write a pre-built JournalEntry to the vault.

        Returns the vault-relative path written, or None if vault is disabled.
        """
        # Fill in identity fields the caller may have omitted
        if not entry.agent_id:
            entry.agent_id = self.agent_id
        if not entry.agent_version:
            entry.agent_version = self.agent_version
        if not entry.trace_id:
            entry.trace_id = self.trace_id
        if not entry.when:
            entry.when = datetime.now(timezone.utc).isoformat()
        if entry.op_sequence == 0:
            self._seq += 1
            entry.op_sequence = self._seq

        self._entries.append(entry)

        if self._vault is None:
            return None

        vault_path = self._vault.vault_path
        note_dir = vault_path / self.vault_subdir / _safe_dir(self.trace_id)
        note_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{entry.op_sequence:04d}-{_slug(entry.what)}.md"
        file_path = note_dir / filename

        markdown = _render_note(entry)
        _atomic_write(file_path, markdown)

        # Keep vault index in sync
        rel_path = str(file_path.relative_to(vault_path))
        self._vault.upsert_note(rel_path, markdown, _frontmatter(entry, self.task_id))

        return file_path

    # ---------------------------------------------------------------- read-back

    def entries(self) -> list[JournalEntry]:
        """Return all entries recorded this session (in sequence order)."""
        return list(self._entries)

    def last_entry(self) -> JournalEntry | None:
        """Return the most recent entry, or None."""
        return self._entries[-1] if self._entries else None

    def causality_chain(self, entry_id: str) -> list[JournalEntry]:
        """Walk triggered_by links from ``entry_id`` back to the root.

        Returns the chain oldest-first (root at index 0).
        """
        by_id = {e.id: e for e in self._entries}
        chain: list[JournalEntry] = []
        current = by_id.get(entry_id)
        while current is not None:
            chain.append(current)
            current = by_id.get(current.triggered_by or "")
        chain.reverse()
        return chain

    def summary(self) -> dict[str, Any]:
        """High-level stats for this journal session."""
        outcomes = [e.outcome for e in self._entries]
        return {
            "agent_id": self.agent_id,
            "trace_id": self.trace_id,
            "total_ops": len(self._entries),
            "success": outcomes.count("success"),
            "failure": outcomes.count("failure"),
            "partial": outcomes.count("partial"),
            "pending": outcomes.count("pending"),
            "total_duration_ms": round(sum(e.duration_ms for e in self._entries), 2),
        }


# ------------------------------------------------------------------ rendering


def _render_note(entry: JournalEntry) -> str:
    """Render a JournalEntry as a FORGE-compatible Obsidian markdown note."""
    causality = (
        f"[[{entry.triggered_by}]] → `{entry.id}`"
        if entry.triggered_by
        else f"`{entry.id}` *(root operation)*"
    )

    state_before_lines = "\n".join(
        f"  - **{k}**: `{v}`" for k, v in (entry.state_before or {}).items()
    ) or "  *(not recorded)*"

    state_after_lines = "\n".join(
        f"  - **{k}**: `{v}`" for k, v in (entry.state_after or {}).items()
    ) or "  *(not recorded)*"

    error_section = (
        f"\n\n## Error\n\n```\n{entry.error}\n```" if entry.error else ""
    )

    notes_section = (
        f"\n\n## Annotations\n\n{entry.notes}" if entry.notes.strip() else ""
    )

    outcome_badge = {
        "success": "✅ success",
        "failure": "❌ failure",
        "partial": "⚠️ partial",
        "pending": "⏳ pending",
    }.get(entry.outcome, entry.outcome)

    return f"""\
# Journal: {entry.what}

| Field | Value |
|---|---|
| **Outcome** | {outcome_badge} |
| **When** | `{entry.when}` |
| **Duration** | `{entry.duration_ms} ms` |
| **Sequence** | `#{entry.op_sequence:04d}` in trace `{entry.trace_id[:8]}…` |
| **Causality** | {causality} |

---

## WHAT

> {entry.what}

## WHY

> {entry.why}

## HOW

> {entry.how}

## State Before

{state_before_lines}

## State After

{state_after_lines}
{error_section}{notes_section}
"""


def _frontmatter(entry: JournalEntry, task_id: str = "") -> dict:
    return {
        "id": entry.id,
        "type": "agent-thinking",
        "domain": entry.domain,
        "created_at": entry.when,
        "updated_at": entry.when,
        "trace_id": entry.trace_id,
        "task_id": task_id,
        "agent_id": entry.agent_id,
        "agent_version": entry.agent_version,
        "confidence": 1.0,
        "pathway_strength": 0.1,
        "op_sequence": entry.op_sequence,
        "triggered_by": entry.triggered_by or "",
        "what": entry.what,
        "why": entry.why,
        "how": entry.how,
        "outcome": entry.outcome,
        "duration_ms": entry.duration_ms,
        "tags": entry.tags,
    }


# ------------------------------------------------------------------ helpers


def _slug(text: str) -> str:
    return re.sub(r"[^\w-]", "_", text.lower().strip())[:48]


def _safe_dir(text: str) -> str:
    """UUID-safe directory name — keep hyphens, strip anything else."""
    return re.sub(r"[^\w-]", "_", text)[:36]


def _atomic_write(path: Path, content: str) -> None:
    """Write content atomically using a sibling temp file + rename."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)  # POSIX: atomic rename

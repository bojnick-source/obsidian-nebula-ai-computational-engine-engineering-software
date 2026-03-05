"""AgentStatusTable — live DataTable showing all dispatched agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable


@dataclass
class AgentRow:
    agent_id: str
    status: str = "pending"
    phase: str = ""
    confidence: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)


_STATUS_COLORS = {
    "pending": "dim",
    "running": "yellow",
    "complete": "green",
    "failed": "red",
    "degraded": "orange1",
}


class AgentStatusTable(Widget):
    """DataTable of agent statuses, updated on AGENT_DISPATCH / PHASE_END events."""

    DEFAULT_CSS = """
    AgentStatusTable {
        height: 12;
        border: solid $primary;
    }
    """

    agent_count: reactive[int] = reactive(0)

    COLUMNS = ("Agent", "Status", "Phase", "Conf", "Tok↑", "Tok↓", "Cost $")

    def __init__(self) -> None:
        super().__init__()
        self._rows: dict[str, AgentRow] = {}

    def compose(self):
        table = DataTable(zebra_stripes=True, cursor_type="row")
        for col in self.COLUMNS:
            table.add_column(col, key=col)
        yield table

    def upsert_agent(self, row: AgentRow) -> None:
        self._rows[row.agent_id] = row
        self.agent_count = len(self._rows)
        self._refresh_table()

    def _refresh_table(self) -> None:
        try:
            table = self.query_one(DataTable)
        except Exception:
            return
        table.clear()
        for r in self._rows.values():
            color = _STATUS_COLORS.get(r.status, "white")
            table.add_row(
                r.agent_id,
                Text(r.status, style=color),
                r.phase,
                f"{r.confidence:.2f}",
                str(r.tokens_in),
                str(r.tokens_out),
                f"{r.cost_usd:.4f}",
            )

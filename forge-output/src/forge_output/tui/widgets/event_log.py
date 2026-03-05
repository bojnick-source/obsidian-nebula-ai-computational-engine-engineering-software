"""EventLog — scrolling raw event log panel."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import RichLog

from forge_output.event_schema import EventType, ForgeEvent


_EVENT_COLORS: dict[EventType, str] = {
    EventType.RUN_START: "bold green",
    EventType.RUN_COMPLETE: "bold green",
    EventType.PHASE_START: "cyan",
    EventType.PHASE_END: "cyan",
    EventType.AGENT_DISPATCH: "yellow",
    EventType.TOOL_START: "blue",
    EventType.TOOL_COMPLETE: "blue",
    EventType.VERIFICATION_GATE: "magenta",
    EventType.DEBATE_ROUND: "orange1",
    EventType.VAULT_WRITE: "green",
    EventType.DEGRADED_MODE: "bold red",
    EventType.ERROR: "bold red",
}


class EventLog(Widget):
    """Compact scrolling log of all events (bottom panel)."""

    DEFAULT_CSS = """
    EventLog {
        height: 8;
        border: solid $surface;
    }
    """

    MAX_LINES = 500

    def __init__(self) -> None:
        super().__init__()
        self._line_count = 0

    def compose(self):
        yield RichLog(highlight=False, markup=True, max_lines=self.MAX_LINES)

    def ingest(self, event: ForgeEvent) -> None:
        color = _EVENT_COLORS.get(event.event_type, "white")
        ts = event.ts.strftime("%H:%M:%S")
        msg = (
            f"[dim]{ts}[/dim] "
            f"[{color}]{event.event_type}[/{color}] "
            f"[dim]{event.phase or event.agent or '—'}[/dim]"
        )
        if event.error_code:
            msg += f" [red]{event.error_code}[/red]"
        try:
            log = self.query_one(RichLog)
            log.write(msg)
        except Exception:
            pass
        self._line_count += 1

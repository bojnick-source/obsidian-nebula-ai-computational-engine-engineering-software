"""ActiveFocusLog — RichLog showing token stream for focused agent."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import RichLog


class ActiveFocusLog(Widget):
    """Streaming token log for the currently active agent."""

    DEFAULT_CSS = """
    ActiveFocusLog {
        height: 1fr;
        border: solid $secondary;
    }
    """

    focused_agent: reactive[str] = reactive("")

    def compose(self):
        yield RichLog(highlight=True, markup=True, wrap=True)

    def watch_focused_agent(self, agent_id: str) -> None:
        try:
            log = self.query_one(RichLog)
            log.clear()
            log.write(f"[bold]Focusing: {agent_id}[/bold]")
        except Exception:
            pass

    def append_token(self, agent_id: str, token: str) -> None:
        if agent_id != self.focused_agent:
            return
        try:
            log = self.query_one(RichLog)
            log.write(token, end="")
        except Exception:
            pass

    def append_message(self, markup: str) -> None:
        try:
            log = self.query_one(RichLog)
            log.write(markup)
        except Exception:
            pass

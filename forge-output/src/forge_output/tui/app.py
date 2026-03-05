"""Textual ForgeApp — 1A: Live TUI pipeline visualization.

Layout (120×40 terminal minimum):
  ┌─ Pipeline Waterfall ─────────────────────────────────┐
  │ PipelineProgressBar (phase bars)                     │
  ├─ Agent Status ───────────────┬─ Active Focus ────────┤
  │ AgentStatusTable             │ ActiveFocusLog        │
  │ (DataTable)                  │ (RichLog, token stream)│
  ├─ Event Log ──────────────────┴───────────────────────┤
  │ EventLog (raw event stream)                          │
  └──────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import zmq
import zmq.asyncio
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from forge_output.event_schema import EventType, ForgeEvent
from forge_output.tui.widgets.active_focus_log import ActiveFocusLog
from forge_output.tui.widgets.agent_status_table import AgentRow, AgentStatusTable
from forge_output.tui.widgets.event_log import EventLog
from forge_output.tui.widgets.pipeline_progress import PipelineProgressBar


class ForgeApp(App):
    """FORGE real-time TUI (Context 1A)."""

    TITLE = "FORGE — Live Pipeline"
    CSS = """
    Screen {
        layout: vertical;
    }
    #middle {
        layout: horizontal;
        height: 1fr;
    }
    #left-panel {
        width: 60%;
    }
    #right-panel {
        width: 40%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f", "focus_next_agent", "Next agent"),
    ]

    def __init__(self, zmq_endpoint: str = "tcp://127.0.0.1:5555") -> None:
        super().__init__()
        self._endpoint = zmq_endpoint
        self._agents_seen: list[str] = []
        self._focus_idx = 0

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        yield PipelineProgressBar(id="pipeline-bar")
        with self.app.compose_context() if False else __import__("contextlib").nullcontext():
            pass
        from textual.containers import Horizontal
        yield Horizontal(
            AgentStatusTable(id="agent-table"),
            ActiveFocusLog(id="focus-log"),
            id="middle",
        )
        yield EventLog(id="event-log")
        yield Footer()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self.run_worker(self._zmq_listener(), exclusive=True, name="zmq")

    # ------------------------------------------------------------------
    # ZMQ async listener
    # ------------------------------------------------------------------

    async def _zmq_listener(self) -> None:
        ctx = zmq.asyncio.Context()
        sock: zmq.asyncio.Socket = ctx.socket(zmq.SUB)
        sock.connect(self._endpoint)
        sock.setsockopt_string(zmq.SUBSCRIBE, "")

        try:
            while True:
                raw: str = await sock.recv_string()
                try:
                    data: dict[str, Any] = json.loads(raw)
                    event = ForgeEvent.from_dict(data)
                    self._dispatch_event(event)
                except Exception:
                    pass
                await asyncio.sleep(0)
        finally:
            sock.close()
            ctx.term()

    # ------------------------------------------------------------------
    # Event routing
    # ------------------------------------------------------------------

    def _dispatch_event(self, event: ForgeEvent) -> None:
        pipeline = self.query_one("#pipeline-bar", PipelineProgressBar)
        table = self.query_one("#agent-table", AgentStatusTable)
        focus = self.query_one("#focus-log", ActiveFocusLog)
        elog = self.query_one("#event-log", EventLog)

        elog.ingest(event)

        match event.event_type:
            case EventType.PHASE_START:
                pipeline.set_active_phase(event.phase)
            case EventType.PHASE_END:
                pipeline.set_phase_progress(event.phase, 1.0)
                pipeline.set_active_phase("")
            case EventType.PROGRESS:
                pipeline.set_phase_progress(event.phase, event.progress)
            case EventType.AGENT_DISPATCH:
                row = AgentRow(
                    agent_id=event.agent,
                    status="running",
                    phase=event.phase,
                    confidence=event.confidence,
                    tokens_in=event.tokens_in,
                    tokens_out=event.tokens_out,
                    cost_usd=event.cost_usd,
                )
                table.upsert_agent(row)
                if event.agent not in self._agents_seen:
                    self._agents_seen.append(event.agent)
                # Auto-focus first agent
                if len(self._agents_seen) == 1:
                    focus.focused_agent = event.agent
            case EventType.TOKEN:
                focus.append_token(event.agent, event.meta.get("token", ""))
            case EventType.VERIFICATION_GATE:
                passed = event.meta.get("passed", True)
                gate = event.meta.get("gate", "unknown")
                color = "green" if passed else "red"
                focus.append_message(
                    f"[{color}]Gate {gate}: {'PASS' if passed else 'FAIL'}[/{color}]"
                )
            case EventType.DEBATE_ROUND:
                focus.append_message(
                    f"[orange1]Debate round {event.meta.get('round', '?')}[/orange1]"
                )
            case EventType.RUN_COMPLETE:
                focus.append_message("[bold green]Run complete.[/bold green]")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_focus_next_agent(self) -> None:
        if not self._agents_seen:
            return
        self._focus_idx = (self._focus_idx + 1) % len(self._agents_seen)
        agent_id = self._agents_seen[self._focus_idx]
        focus = self.query_one("#focus-log", ActiveFocusLog)
        focus.focused_agent = agent_id


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="FORGE Live TUI")
    parser.add_argument("--zmq", default="tcp://127.0.0.1:5555")
    args = parser.parse_args()
    ForgeApp(zmq_endpoint=args.zmq).run()


if __name__ == "__main__":
    main()

"""PipelineProgressBar widget — top-of-screen waterfall view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import ProgressBar, Static


PHASES = [
    "intake",
    "skill_routing",
    "decomposition",
    "memory_preflight",
    "specialist",
    "antagonist",
    "tool_execution",
    "verification",
    "persistence",
    "output",
]


class PhaseBar(Widget):
    """Single phase bar with label and progress."""

    DEFAULT_CSS = """
    PhaseBar {
        height: 1;
        layout: horizontal;
    }
    PhaseBar .label {
        width: 20;
        content-align: left middle;
    }
    PhaseBar ProgressBar {
        width: 1fr;
    }
    """

    progress: reactive[float] = reactive(0.0)
    active: reactive[bool] = reactive(False)

    def __init__(self, phase_name: str) -> None:
        super().__init__()
        self._phase_name = phase_name

    def compose(self) -> ComposeResult:
        yield Static(self._phase_name, classes="label")
        yield ProgressBar(total=100, show_eta=False)

    def watch_progress(self, value: float) -> None:
        bar = self.query_one(ProgressBar)
        bar.progress = value * 100

    def watch_active(self, value: bool) -> None:
        self.set_class(value, "active")


class PipelineProgressBar(Widget):
    """Waterfall view of all pipeline phases."""

    DEFAULT_CSS = """
    PipelineProgressBar {
        height: auto;
        border: solid $accent;
        padding: 0 1;
    }
    PipelineProgressBar .active {
        background: $accent 20%;
    }
    """

    def compose(self) -> ComposeResult:
        for phase in PHASES:
            yield PhaseBar(phase, id=f"phase-{phase}")

    def set_phase_progress(self, phase: str, progress: float) -> None:
        try:
            bar = self.query_one(f"#phase-{phase}", PhaseBar)
            bar.progress = progress
        except Exception:
            pass

    def set_active_phase(self, phase: str) -> None:
        for p in PHASES:
            try:
                bar = self.query_one(f"#phase-{p}", PhaseBar)
                bar.active = p == phase
            except Exception:
                pass

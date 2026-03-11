"""Plotly interactive HTML elements for engineering reports."""

from __future__ import annotations

from typing import Sequence

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False


def stress_distribution_histogram(
    stress_values: Sequence[float],
    yield_strength: float,
    title: str = "von Mises Stress Distribution",
) -> str:
    """Return Plotly div HTML for embedding in a report."""
    if not _PLOTLY_AVAILABLE:
        return "<p>plotly not installed</p>"

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=list(stress_values), name="von Mises [MPa]"))
    fig.add_vline(
        x=yield_strength,
        line_dash="dash",
        line_color="red",
        annotation_text=f"σ_y = {yield_strength} MPa",
    )
    fig.update_layout(
        title=title,
        xaxis_title="von Mises Stress [MPa]",
        yaxis_title="Element Count",
        template="plotly_white",
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def load_displacement_scatter(
    loads: Sequence[float],
    displacements: Sequence[float],
    title: str = "Load vs Displacement",
) -> str:
    """Return Plotly div HTML for load-displacement curve."""
    if not _PLOTLY_AVAILABLE:
        return "<p>plotly not installed</p>"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(loads), y=list(displacements), mode="lines+markers"))
    fig.update_layout(
        title=title,
        xaxis_title="Load [N]",
        yaxis_title="Displacement [mm]",
        template="plotly_white",
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

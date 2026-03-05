"""2D convergence plots, S-N curves, and mesh study charts via matplotlib."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for off-screen use
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def plot_convergence_history(
    iterations: Sequence[int],
    residuals: Sequence[float],
    output_png: Path,
    title: str = "Solver Convergence",
    threshold: float = 1e-4,
) -> Path:
    """Plot residual convergence on a log scale."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.semilogy(iterations, residuals, "b-", linewidth=1.5, label="Residual")
    ax.axhline(threshold, color="r", linestyle="--", label=f"Target {threshold:.0e}")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Residual")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(str(output_png), dpi=150)
    plt.close(fig)
    return output_png


def plot_mesh_convergence(
    element_counts: Sequence[int],
    qoi_values: Sequence[float],
    output_png: Path,
    qoi_label: str = "Max von Mises [MPa]",
    gci_band: tuple[float, float] | None = None,
) -> Path:
    """Plot mesh convergence study (QoI vs element count)."""
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(element_counts, qoi_values, "ko-", markersize=6, label=qoi_label)
    if gci_band is not None:
        lo, hi = gci_band
        ax.axhspan(lo, hi, alpha=0.15, color="green", label="GCI band (95%)")
    ax.set_xlabel("Element count")
    ax.set_ylabel(qoi_label)
    ax.set_title("Mesh Convergence Study")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x/1e3:.0f}k"))
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(str(output_png), dpi=150)
    plt.close(fig)
    return output_png


def plot_sn_curve(
    stress_amplitudes: Sequence[float],
    cycles_to_failure: Sequence[float],
    material_label: str,
    output_png: Path,
    design_point: tuple[float, float] | None = None,
) -> Path:
    """Log-log S-N (Wöhler) fatigue curve."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(cycles_to_failure, stress_amplitudes, "b-", label=f"S-N: {material_label}")
    if design_point is not None:
        n_dp, s_dp = design_point
        ax.loglog(n_dp, s_dp, "rv", markersize=10, label=f"Design point ({n_dp:.0e} cycles)")
    ax.set_xlabel("Cycles to Failure N")
    ax.set_ylabel("Stress Amplitude [MPa]")
    ax.set_title("S-N Fatigue Curve")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(str(output_png), dpi=150)
    plt.close(fig)
    return output_png

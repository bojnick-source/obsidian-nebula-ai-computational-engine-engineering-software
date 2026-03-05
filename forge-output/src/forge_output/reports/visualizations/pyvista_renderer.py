"""Off-screen 3D stress/displacement plots via PyVista."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import pyvista as pv
    _PYVISTA_AVAILABLE = True
except ImportError:
    _PYVISTA_AVAILABLE = False


def render_von_mises_plot(
    vtk_path: Path,
    output_png: Path,
    scalar_field: str = "S",
    component: str = "Mises",
    cmap: str = "hot",
    window_size: tuple[int, int] = (1200, 800),
) -> Path:
    """Render a von Mises stress contour from a CalculiX VTK result.

    Requires pyvista and a VTK file exported by ccx2paraview.
    Returns output_png path.
    """
    if not _PYVISTA_AVAILABLE:
        raise RuntimeError("pyvista not installed")

    pv.start_xvfb()  # headless X for off-screen rendering
    mesh = pv.read(str(vtk_path))

    plotter = pv.Plotter(off_screen=True, window_size=list(window_size))
    plotter.add_mesh(
        mesh,
        scalars=scalar_field,
        component=component,
        cmap=cmap,
        show_scalar_bar=True,
        scalar_bar_args={"title": "von Mises [MPa]"},
    )
    plotter.add_axes()
    plotter.show(screenshot=str(output_png), auto_close=False)
    plotter.close()
    return output_png


def render_displacement_plot(
    vtk_path: Path,
    output_png: Path,
    displacement_field: str = "U",
    scale_factor: float = 100.0,
    window_size: tuple[int, int] = (1200, 800),
) -> Path:
    """Render displacement magnitude with exaggerated deformation."""
    if not _PYVISTA_AVAILABLE:
        raise RuntimeError("pyvista not installed")

    pv.start_xvfb()
    mesh = pv.read(str(vtk_path))
    warped = mesh.warp_by_vector(displacement_field, factor=scale_factor)

    plotter = pv.Plotter(off_screen=True, window_size=list(window_size))
    plotter.add_mesh(
        warped,
        scalars=displacement_field,
        cmap="coolwarm",
        show_scalar_bar=True,
        scalar_bar_args={"title": f"Displacement [mm] (×{scale_factor:.0f})"},
    )
    plotter.add_axes()
    plotter.show(screenshot=str(output_png), auto_close=False)
    plotter.close()
    return output_png

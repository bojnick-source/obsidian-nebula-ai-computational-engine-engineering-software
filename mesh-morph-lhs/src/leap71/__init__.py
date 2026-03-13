"""
leap71 — LEAP71 computational engineering libraries grafted into the core.

C# source trees live alongside this file and are compiled via dotnet.
Python layer imports this package to locate the C# project roots and
invoke dotnet tasks directly — single polyglot pipeline, no translation.

Libraries included (C# source, unmodified):
  PicoGK/          — voxel geometry kernel
  ShapeKernel/     — BaseShapes, LocalFrame, Boolean ops (Sh)
  LatticeLibrary/  — ICellArray / ILatticeType / IBeamThickness + TPMS
  QuasiCrystals/   — PenrosePattern, QuasiTile hierarchy, IcosahedralFace
  RoverWheel/      — WheelLayer, WheelElements, ITreadPattern, WheelTread
  HelixHeatX/      — Helix heat-exchanger CEM (inverse design reference)

Sources: https://github.com/leap71
"""

from pathlib import Path

# Root of this package — all C# trees are siblings of this file.
LEAP71_ROOT: Path = Path(__file__).parent

PICOGK_ROOT:          Path = LEAP71_ROOT / "PicoGK"
SHAPE_KERNEL_ROOT:    Path = LEAP71_ROOT / "ShapeKernel"
LATTICE_LIBRARY_ROOT: Path = LEAP71_ROOT / "LatticeLibrary"
QUASI_CRYSTALS_ROOT:  Path = LEAP71_ROOT / "QuasiCrystals"
ROVER_WHEEL_ROOT:     Path = LEAP71_ROOT / "RoverWheel"
HELIX_HEAT_X_ROOT:    Path = LEAP71_ROOT / "HelixHeatX"

__all__ = [
    "LEAP71_ROOT",
    "PICOGK_ROOT",
    "SHAPE_KERNEL_ROOT",
    "LATTICE_LIBRARY_ROOT",
    "QUASI_CRYSTALS_ROOT",
    "ROVER_WHEEL_ROOT",
    "HELIX_HEAT_X_ROOT",
]

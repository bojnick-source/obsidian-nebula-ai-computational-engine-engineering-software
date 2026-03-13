"""forge-solver: FORGE numerical engineering solvers.

Provides:
  atmosphere  — ISA atmosphere model, lift/drag, range/endurance
  bemt        — Blade Element Momentum Theory rotor solver
  fea         — Euler-Bernoulli FEA beam solver
  topology    — Structural topology optimization (SIMP, ground-structure, divergent)
  smart_fuselage — Parametric smart airframe: aero, structure, embedded systems

Language policy (polyglot):
  Python  — orchestration, data models, agent integration
  C++20   — accuracy-critical inner loops (see forge-core/src/solver/)

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/reidce/)
"""

from __future__ import annotations

__version__ = "0.1.0"

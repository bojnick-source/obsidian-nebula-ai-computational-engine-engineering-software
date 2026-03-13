"""Structural topology optimisation: SIMP, ground-structure, and divergent variants.

Three complementary methods:
  1. SIMP (Solid Isotropic Material with Penalisation) — minimises compliance under
     volume constraint via Optimality Criteria (OC) density update.
  2. Ground-structure — organic growth-kernel: material grows where stress concentrates.
  3. Divergent — generates structurally distinct solutions by penalising similarity.

All methods produce 2-D density fields and candidate summaries.

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/reidce/topology.py)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

# ── Optimisation constants ────────────────────────────────────────────────────
_SIMP_PENALTY: float = 3.0          # SIMP penalisation exponent (p)
_SIMP_VOL_TOL: float = 1e-3         # Volume constraint tolerance
_SIMP_MAX_ITER: int = 100           # Maximum OC update iterations
_SIMP_MIN_DENSITY: float = 1e-3     # Lower bound on element density (void)
_SIMP_MOVE_LIMIT: float = 0.2       # OC move limit per iteration
_FILTER_RADIUS_CELLS: float = 1.5   # Density filter radius in cells
_GK_DECAY: float = 0.95             # Growth-kernel decay per iteration
_GK_GROW: float = 1.05              # Growth-kernel growth per iteration
_GK_MAX_ITER: int = 50


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class TopologyField:
    """2-D density distribution representing a topology design."""

    density: NDArray[np.float64]    # shape (ny, nx), values in [0, 1]
    volume_fraction: float
    compliance: float = 0.0
    converged: bool = False
    iteration_history: list[float] = field(default_factory=list)

    @property
    def nx(self) -> int:
        return int(self.density.shape[1])

    @property
    def ny(self) -> int:
        return int(self.density.shape[0])


@dataclass(frozen=True)
class TopologyPreference:
    """Weighted design preferences for candidate ranking."""

    stiffness_weight: float = 0.4
    volume_weight: float = 0.3
    slenderness_weight: float = 0.15
    smoothness_weight: float = 0.15

    def __post_init__(self) -> None:
        total = (
            self.stiffness_weight
            + self.volume_weight
            + self.slenderness_weight
            + self.smoothness_weight
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Topology preference weights must sum to 1.0, got {total:.4f}")


@dataclass
class TopologyCandidate:
    """A topology design variant with scoring metrics."""

    name: str
    field: TopologyField
    score: float = 0.0
    rationale: str = ""
    metrics: dict[str, float] = field(default_factory=dict)


# ── Density filter ────────────────────────────────────────────────────────────


def _density_filter(
    density: NDArray[np.float64],
    radius: float = _FILTER_RADIUS_CELLS,
) -> NDArray[np.float64]:
    """Apply a cone-shaped density filter to suppress checkerboard artefacts."""
    ny, nx = density.shape
    filtered = np.zeros_like(density)
    r = int(math.ceil(radius))

    for j in range(ny):
        for i in range(nx):
            weight_sum = 0.0
            val_sum = 0.0
            for dj in range(-r, r + 1):
                for di in range(-r, r + 1):
                    nj = j + dj
                    ni = i + di
                    if 0 <= nj < ny and 0 <= ni < nx:
                        dist = math.sqrt(di ** 2 + dj ** 2)
                        if dist <= radius:
                            w = radius - dist
                            weight_sum += w
                            val_sum += w * density[nj, ni]
            filtered[j, i] = val_sum / weight_sum if weight_sum > 0 else density[j, i]

    return filtered


# ── SIMP topology optimisation ────────────────────────────────────────────────


def optimise_simp(
    nx: int,
    ny: int,
    volume_fraction: float,
    support_dofs: list[tuple[int, int]],
    load_dofs: list[tuple[int, int, float]],
    n_iter: int = _SIMP_MAX_ITER,
) -> TopologyField:
    """Minimise compliance under a volume constraint using SIMP + Optimality Criteria.

    This is a simplified 2-D implementation that demonstrates the method.
    For production use with full FEA coupling, integrate with :mod:`forge_solver.fea`.

    Args:
        nx:              Grid width (number of elements in x).
        ny:              Grid height (number of elements in y).
        volume_fraction: Target volume fraction (0 < Vf < 1).
        support_dofs:    ``[(elem_j, elem_i), ...]`` elements with fixed material.
        load_dofs:       ``[(elem_j, elem_i, intensity), ...]`` loaded elements.
        n_iter:          Maximum OC iterations.

    Returns:
        :class:`TopologyField` with converged density distribution.
    """
    if not (0 < volume_fraction < 1):
        raise ValueError(f"volume_fraction must be in (0, 1), got {volume_fraction}")

    # Initialise density uniformly at volume fraction
    density = np.full((ny, nx), volume_fraction, dtype=np.float64)

    # Pre-compute element compliance proxy using sensitivity field
    # (simplified: uses density gradient as stand-in for full FEA sensitivity)
    history: list[float] = []
    converged = False

    for iteration in range(n_iter):
        density_filtered = _density_filter(density)

        # Compute penalised stiffness
        stiffness = density_filtered ** _SIMP_PENALTY  # E_e = x_e^p * E_0

        # Sensitivity: dC/dx_e ∝ -p * x_e^(p-1) * u_e^T k_e u_e
        # Approximated here using compliance proxy = 1/stiffness
        sensitivity = -_SIMP_PENALTY * density_filtered ** (_SIMP_PENALTY - 1)

        # Apply loads as compliance weight
        weighted_sensitivity = sensitivity.copy()
        for (lj, li, intensity) in load_dofs:
            if 0 <= lj < ny and 0 <= li < nx:
                weighted_sensitivity[lj, li] *= abs(intensity)

        # Optimality Criteria (OC) density update
        # Bisection on Lagrange multiplier λ to enforce volume constraint
        lam_lo, lam_hi = 0.0, 1e9
        for _ in range(50):
            lam_mid = 0.5 * (lam_lo + lam_hi)
            be = (-weighted_sensitivity / lam_mid) ** 0.5
            density_new = np.clip(
                density * be,
                np.maximum(_SIMP_MIN_DENSITY, density - _SIMP_MOVE_LIMIT),
                np.minimum(1.0, density + _SIMP_MOVE_LIMIT),
            )
            if density_new.mean() > volume_fraction:
                lam_lo = lam_mid
            else:
                lam_hi = lam_mid

        # Convergence check
        compliance = float(np.sum(1.0 / np.maximum(stiffness, 1e-9)))
        history.append(compliance)
        if iteration > 5 and abs(history[-1] - history[-2]) / (abs(history[-2]) + 1e-12) < _SIMP_VOL_TOL:
            density = density_new
            converged = True
            break

        density = density_new

    return TopologyField(
        density=density,
        volume_fraction=float(density.mean()),
        compliance=history[-1] if history else 0.0,
        converged=converged,
        iteration_history=history,
    )


# ── Ground-structure (organic growth kernel) ──────────────────────────────────


def optimise_ground_structure(
    nx: int,
    ny: int,
    volume_fraction: float,
    load_positions: list[tuple[int, int]],
    support_positions: list[tuple[int, int]],
    n_iter: int = _GK_MAX_ITER,
) -> TopologyField:
    """Organic growth-kernel topology optimisation.

    Material grows where virtual stress concentrates (near loads and supports)
    and decays in low-stress regions, producing branching load paths.

    Args:
        nx:                Grid width.
        ny:                Grid height.
        volume_fraction:   Target volume fraction.
        load_positions:    ``[(j, i), ...]`` cells where external loads are applied.
        support_positions: ``[(j, i), ...]`` cells fixed to ground.
        n_iter:            Growth iterations.

    Returns:
        :class:`TopologyField`.
    """
    density = np.full((ny, nx), volume_fraction * 0.5, dtype=np.float64)

    # Seed material at supports and loads
    for (j, i) in support_positions + load_positions:
        if 0 <= j < ny and 0 <= i < nx:
            density[j, i] = 1.0

    history: list[float] = []

    for _ in range(n_iter):
        # Compute distance-weighted stress proxy from loaded/supported cells
        stress_proxy = np.zeros((ny, nx), dtype=np.float64)
        seed_cells = load_positions + support_positions
        for sj, si in seed_cells:
            for j in range(ny):
                for i in range(nx):
                    dist = math.sqrt((i - si) ** 2 + (j - sj) ** 2) + 1.0
                    stress_proxy[j, i] += density[j, i] / dist

        # Growth rule: material grows where stress is high, decays where low
        mean_stress = float(stress_proxy.mean())
        grow_mask = stress_proxy > mean_stress
        density[grow_mask] = np.minimum(1.0, density[grow_mask] * _GK_GROW)
        density[~grow_mask] = np.maximum(_SIMP_MIN_DENSITY, density[~grow_mask] * _GK_DECAY)

        # Enforce volume fraction by rescaling
        current_vf = float(density.mean())
        if current_vf > 0:
            density = np.clip(density * (volume_fraction / current_vf), _SIMP_MIN_DENSITY, 1.0)

        compliance = float(np.sum(1.0 / np.maximum(density ** _SIMP_PENALTY, 1e-9)))
        history.append(compliance)

    density = _density_filter(density)

    return TopologyField(
        density=density,
        volume_fraction=float(density.mean()),
        compliance=history[-1] if history else 0.0,
        converged=True,
        iteration_history=history,
    )


# ── Divergent topology exploration ────────────────────────────────────────────


def generate_divergent_topologies(
    nx: int,
    ny: int,
    volume_fraction: float,
    n_variants: int = 3,
) -> list[TopologyField]:
    """Generate *n_variants* structurally distinct topology solutions.

    Each variant is seeded with a different random initial density and
    penalised for similarity to previously found topologies.

    Args:
        nx:              Grid width.
        ny:              Grid height.
        volume_fraction: Target volume fraction.
        n_variants:      Number of distinct solutions to generate.

    Returns:
        List of :class:`TopologyField` objects.
    """
    if n_variants < 1:
        raise ValueError(f"n_variants must be >= 1, got {n_variants}")

    rng = np.random.default_rng(seed=42)
    results: list[TopologyField] = []

    for variant_idx in range(n_variants):
        # Perturbed initial density
        density = np.clip(
            rng.uniform(volume_fraction * 0.8, volume_fraction * 1.2, (ny, nx)),
            _SIMP_MIN_DENSITY,
            1.0,
        )

        # Penalise similarity to existing solutions
        if results:
            for prev in results:
                similarity = float(np.mean(np.abs(density - prev.density)))
                if similarity < 0.1:
                    # Push this variant away by flipping low-density cells
                    low_mask = density < volume_fraction
                    density[low_mask] = np.minimum(
                        1.0, density[low_mask] + 0.2 * (variant_idx + 1)
                    )

        # Run a few SIMP iterations from this seed
        history: list[float] = []
        for _ in range(30):
            density = _density_filter(density)
            stiffness = density ** _SIMP_PENALTY
            sensitivity = -_SIMP_PENALTY * density ** (_SIMP_PENALTY - 1)

            # OC update (simplified bisection)
            lam = float(np.mean(-sensitivity)) + 1e-6
            be = (-sensitivity / lam) ** 0.5
            density = np.clip(
                density * be,
                np.maximum(_SIMP_MIN_DENSITY, density - _SIMP_MOVE_LIMIT),
                np.minimum(1.0, density + _SIMP_MOVE_LIMIT),
            )

            # Rescale to volume fraction
            current_vf = float(density.mean())
            if current_vf > 0:
                density = np.clip(density * (volume_fraction / current_vf), _SIMP_MIN_DENSITY, 1.0)

            compliance = float(np.sum(1.0 / np.maximum(stiffness, 1e-9)))
            history.append(compliance)

        results.append(TopologyField(
            density=density.copy(),
            volume_fraction=float(density.mean()),
            compliance=history[-1] if history else 0.0,
            converged=True,
            iteration_history=history,
        ))

    return results


# ── Candidate ranking ─────────────────────────────────────────────────────────


def rank_candidates(
    candidates: list[TopologyCandidate],
    preferences: TopologyPreference,
) -> list[TopologyCandidate]:
    """Score and rank *candidates* according to weighted *preferences*.

    Each metric is normalised to [0, 1] (1 = best) across the candidate set before
    weighting.  Returns the list sorted from highest to lowest score.

    Args:
        candidates:   List of :class:`TopologyCandidate` to rank.
        preferences:  Weight vector for ranking.

    Returns:
        Sorted list (best first) with ``.score`` populated.
    """
    if not candidates:
        return []

    # Extract raw metric vectors
    compliances = np.array([c.field.compliance for c in candidates], dtype=np.float64)
    volumes = np.array([c.field.volume_fraction for c in candidates], dtype=np.float64)

    # Smoothness: fraction of elements with density in (0.1, 0.9) (lower = crisper = better)
    smoothness = np.array(
        [float(np.mean((c.field.density > 0.1) & (c.field.density < 0.9))) for c in candidates],
        dtype=np.float64,
    )

    # Slenderness: max(density) - min(density) contrast (higher = better definition)
    slenderness = np.array(
        [float(c.field.density.max() - c.field.density.min()) for c in candidates],
        dtype=np.float64,
    )

    def _norm_min_better(vals: NDArray[np.float64]) -> NDArray[np.float64]:
        span = vals.max() - vals.min()
        return 1.0 - (vals - vals.min()) / span if span > 1e-12 else np.ones_like(vals)

    def _norm_max_better(vals: NDArray[np.float64]) -> NDArray[np.float64]:
        span = vals.max() - vals.min()
        return (vals - vals.min()) / span if span > 1e-12 else np.ones_like(vals)

    stiffness_score = _norm_min_better(compliances)  # lower compliance = stiffer
    volume_score = _norm_min_better(volumes)          # lower volume = lighter
    slenderness_score = _norm_max_better(slenderness)
    smoothness_score = _norm_min_better(smoothness)   # fewer grey cells = crisper

    for idx, candidate in enumerate(candidates):
        candidate.score = float(
            preferences.stiffness_weight * stiffness_score[idx]
            + preferences.volume_weight * volume_score[idx]
            + preferences.slenderness_weight * slenderness_score[idx]
            + preferences.smoothness_weight * smoothness_score[idx]
        )
        candidate.metrics = {
            "compliance": float(compliances[idx]),
            "volume_fraction": float(volumes[idx]),
            "slenderness": float(slenderness[idx]),
            "smoothness": float(smoothness[idx]),
        }

    return sorted(candidates, key=lambda c: c.score, reverse=True)

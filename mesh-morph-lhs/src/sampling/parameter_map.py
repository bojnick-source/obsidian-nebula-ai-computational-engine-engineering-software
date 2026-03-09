"""ParameterSpec dataclass and sample-to-params mapping.

Supports three transform types:
    linear  — simple affine mapping p = lo + u*(hi-lo)
    log     — exponential mapping p = lo * (hi/lo)^u  (useful for thickness, area)
    angle   — same as linear but semantically tagged as an angle in degrees
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ParameterSpec:
    """Definition of one design variable."""
    name: str
    lower: float
    upper: float
    transform: str = "linear"   # "linear" | "log" | "angle"

    def map(self, u: float) -> float:
        """Map a unit-interval value u ∈ [0,1] to the physical parameter value."""
        u = float(np.clip(u, 0.0, 1.0))
        if self.transform == "log":
            if self.lower <= 0 or self.upper <= 0:
                raise ValueError(f"log transform requires positive bounds for {self.name}")
            return float(self.lower * (self.upper / self.lower) ** u)
        else:
            # linear and angle both use affine mapping
            return float(self.lower + u * (self.upper - self.lower))

    def unmap(self, p: float) -> float:
        """Inverse: physical value → unit interval (for normalising archive data)."""
        if self.transform == "log":
            if self.lower <= 0 or self.upper <= 0:
                return 0.5
            log_lo, log_hi = np.log(self.lower), np.log(self.upper)
            log_p = np.log(max(p, 1e-300))
            return float(np.clip((log_p - log_lo) / (log_hi - log_lo), 0.0, 1.0))
        else:
            span = self.upper - self.lower
            if abs(span) < 1e-12:
                return 0.5
            return float(np.clip((p - self.lower) / span, 0.0, 1.0))


def specs_from_config(cfg_params: list) -> list[ParameterSpec]:
    """Build ParameterSpec list from the 'parameters' section of design_space.yaml.

    Each entry is [name, lower, upper] or [name, lower, upper, transform].
    """
    specs: list[ParameterSpec] = []
    for entry in cfg_params:
        name = str(entry[0])
        lo = float(entry[1])
        hi = float(entry[2])
        transform = str(entry[3]) if len(entry) > 3 else "linear"
        specs.append(ParameterSpec(name=name, lower=lo, upper=hi, transform=transform))
    return specs


def map_sample_to_params(u_row: np.ndarray, specs: list[ParameterSpec]) -> dict:
    """Map a single LHS row (n_dim values in [0,1]) to a named param dict."""
    return {spec.name: spec.map(float(u)) for spec, u in zip(specs, u_row)}


def normalise_params(params: dict, specs: list[ParameterSpec]) -> np.ndarray:
    """Convert a physical param dict back to a unit-interval row vector."""
    return np.array([spec.unmap(params[spec.name]) for spec in specs])


def normalise_archive(archive: list[dict], specs: list[ParameterSpec]) -> np.ndarray:
    """Stack normalised parameter vectors for all archive entries."""
    return np.stack([normalise_params(r["params"], specs) for r in archive])

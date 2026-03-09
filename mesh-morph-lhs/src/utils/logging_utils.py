"""Structured logging helpers for the morphogenesis pipeline."""

from __future__ import annotations

import logging
import sys
import time


def get_logger(name: str = "mesh_morph") -> logging.Logger:
    """Return a configured logger with a clean console formatter."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-7s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


class GenerationTimer:
    """Context-manager that logs timing for each pipeline phase."""

    def __init__(self, label: str, logger: logging.Logger | None = None) -> None:
        self._label = label
        self._logger = logger or get_logger()
        self._start = 0.0

    def __enter__(self) -> "GenerationTimer":
        self._start = time.perf_counter()
        self._logger.info(f"► {self._label}")
        return self

    def __exit__(self, *args: object) -> None:
        elapsed = time.perf_counter() - self._start
        self._logger.info(f"  ✓ {self._label} — {elapsed:.2f}s")


def log_generation_summary(
    gen: int,
    n_total: int,
    n_feasible: int,
    n_infeasible: int,
    best_score: float,
    best_compliance: float | None = None,
    best_mass: float | None = None,
    logger: logging.Logger | None = None,
) -> None:
    log = logger or get_logger()
    log.info(
        f"Gen {gen:3d} | total={n_total:4d}  feasible={n_feasible:4d}"
        f"  invalid={n_infeasible:4d} | best_score={best_score:.5f}"
        + (f"  compliance={best_compliance:.4e}" if best_compliance is not None else "")
        + (f"  mass={best_mass:.4e}" if best_mass is not None else "")
    )


def log_sample_progress(
    sample_idx: int,
    n_total: int,
    feasible: bool,
    score: float,
    reason: str = "ok",
    logger: logging.Logger | None = None,
) -> None:
    log = logger or get_logger()
    status = "✓" if feasible else "✗"
    score_str = f"{score:.4f}" if score < 1e8 else "inf"
    log.debug(
        f"  [{sample_idx + 1:4d}/{n_total}] {status}  score={score_str}"
        + (f"  ({reason})" if not feasible else "")
    )

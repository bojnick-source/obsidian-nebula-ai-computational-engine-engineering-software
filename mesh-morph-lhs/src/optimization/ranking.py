"""Pareto front sorting and candidate ranking.

Implements:
    non_dominated_sort — fast non-dominated sorting (NSGA-II style)
    pareto_front       — first front only
    rank_archive       — full ranking by (pareto_rank, scalar_score)
"""

from __future__ import annotations

import numpy as np


# ── Non-dominated sorting ─────────────────────────────────────────────────────

def dominates(a: np.ndarray, b: np.ndarray) -> bool:
    """Return True if vector a dominates vector b (minimisation).

    a dominates b iff:
        ∀i: a[i] <= b[i]   AND
        ∃i: a[i] < b[i]
    """
    return bool(np.all(a <= b) and np.any(a < b))


def non_dominated_sort(obj_matrix: np.ndarray) -> list[list[int]]:
    """Assign Pareto rank to each row of obj_matrix (minimisation).

    Parameters
    ----------
    obj_matrix : (N, K) array
        Each row is a feasible candidate's objective vector.

    Returns
    -------
    fronts : list of lists of row indices
        fronts[0] = Pareto front (rank 1)
        fronts[1] = rank 2, etc.
    """
    n = len(obj_matrix)
    dominated_count = np.zeros(n, dtype=int)   # S_p in NSGA-II
    dominates_set: list[list[int]] = [[] for _ in range(n)]
    fronts: list[list[int]] = [[]]

    for i in range(n):
        for j in range(i + 1, n):
            if dominates(obj_matrix[i], obj_matrix[j]):
                dominates_set[i].append(j)
                dominated_count[j] += 1
            elif dominates(obj_matrix[j], obj_matrix[i]):
                dominates_set[j].append(i)
                dominated_count[i] += 1

    for i in range(n):
        if dominated_count[i] == 0:
            fronts[0].append(i)

    current = 0
    while fronts[current]:
        next_front: list[int] = []
        for i in fronts[current]:
            for j in dominates_set[i]:
                dominated_count[j] -= 1
                if dominated_count[j] == 0:
                    next_front.append(j)
        current += 1
        fronts.append(next_front)

    return [f for f in fronts if f]


def pareto_front(results: list[dict], objectives: tuple[str, str] = ("compliance", "mass")) -> list[dict]:
    """Return the non-dominated Pareto front from a list of feasible results."""
    feasible = [r for r in results if r.get("feasible") and r.get("objectives")]
    if not feasible:
        return []

    obj_names = list(objectives)
    obj_matrix = np.array([[r["objectives"][k] for k in obj_names] for r in feasible])

    fronts = non_dominated_sort(obj_matrix)
    if not fronts:
        return []

    return [feasible[i] for i in fronts[0]]


# ── Full archive ranking ──────────────────────────────────────────────────────

def rank_archive(archive: list[dict], pareto_objectives: list[str] | None = None) -> list[dict]:
    """Sort the full archive by (pareto_rank ASC, score ASC).

    Infeasible candidates are appended at the end, sorted by reason.

    Parameters
    ----------
    archive:
        Complete list of evaluated results, feasible and infeasible.
    pareto_objectives:
        Names of objective keys to use for Pareto sorting.
        Defaults to ["compliance", "mass"].

    Returns
    -------
    Sorted list with a "rank" field added to each entry.
    """
    obj_keys = pareto_objectives or ["compliance", "mass"]

    feasible = [r for r in archive if r.get("feasible") and r.get("objectives")]
    infeasible = [r for r in archive if not r.get("feasible")]

    # Compute Pareto ranks for feasible candidates
    if feasible:
        obj_matrix = np.array([[r["objectives"][k] for k in obj_keys] for r in feasible])
        fronts = non_dominated_sort(obj_matrix)
        pareto_rank = np.zeros(len(feasible), dtype=int)
        for rank_idx, front in enumerate(fronts, start=1):
            for i in front:
                pareto_rank[i] = rank_idx
        for i, r in enumerate(feasible):
            r = dict(r)
            r["pareto_rank"] = int(pareto_rank[i])
            feasible[i] = r

    # Sort feasible by (pareto_rank, aggregate score)
    feasible.sort(key=lambda r: (r.get("pareto_rank", 999), r.get("score", float("inf"))))

    # Assign final rank
    for final_rank, r in enumerate(feasible, start=1):
        r["rank"] = final_rank

    for r in infeasible:
        r["rank"] = len(feasible) + 1
        r["pareto_rank"] = -1

    return feasible + infeasible


def select_elite(results: list[dict], elite_fraction: float = 0.20) -> list[dict]:
    """Return the top-elite_fraction of feasible results by score."""
    feasible = sorted(
        [r for r in results if r.get("feasible")],
        key=lambda r: r.get("score", float("inf")),
    )
    n_elite = max(1, int(len(feasible) * elite_fraction))
    return feasible[:n_elite]

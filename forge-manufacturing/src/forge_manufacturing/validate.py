"""Spec validation and topological sort for manufacturing process flows.

Provides:
  load_spec()       — load and Pydantic-validate a YAML spec file
  topological_sort() — Kahn's algorithm DAG sort of process steps
  validate_spec()   — public entry-point running all checks

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/sfcs_mdp/validate.py)
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

import yaml

from forge_manufacturing.model import ProcessStep, Spec


class SpecValidationError(ValueError):
    """Raised when a spec file fails structural or consistency validation."""


def load_spec(path: Path) -> Spec:
    """Load and validate a YAML manufacturing spec file.

    Args:
        path: Path to the ``.yaml`` spec file.

    Returns:
        Validated :class:`~forge_manufacturing.model.Spec` instance.

    Raises:
        FileNotFoundError: If *path* does not exist.
        SpecValidationError: If the YAML is empty or fails Pydantic validation.
    """
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        raise SpecValidationError(f"Spec file is empty: {path}")
    try:
        return Spec.model_validate(data)
    except Exception as exc:
        raise SpecValidationError(f"Spec validation failed for {path}: {exc}") from exc


def _ensure_unique_step_ids(steps: list[ProcessStep]) -> None:
    """Raise if any two steps share the same step_id.

    Raises:
        SpecValidationError: With all duplicate IDs listed.
    """
    seen: set[str] = set()
    duplicates: list[str] = []
    for step in steps:
        if step.step_id in seen:
            duplicates.append(step.step_id)
        seen.add(step.step_id)
    if duplicates:
        raise SpecValidationError(
            f"Duplicate step IDs found: {sorted(set(duplicates))}"
        )


def _ensure_prerequisites_exist(steps: list[ProcessStep]) -> None:
    """Raise if any step references a prerequisite step_id that is not defined.

    Raises:
        SpecValidationError: With all missing prerequisite IDs listed.
    """
    defined: set[str] = {s.step_id for s in steps}
    missing: list[str] = []
    for step in steps:
        for prereq in step.prerequisites:
            if prereq not in defined:
                missing.append(f"{step.step_id} -> {prereq}")
    if missing:
        raise SpecValidationError(
            f"Steps reference undefined prerequisites: {sorted(missing)}"
        )


def topological_sort(steps: list[ProcessStep]) -> list[ProcessStep]:
    """Return *steps* in a valid topological execution order (Kahn's algorithm).

    Steps with no prerequisites come first; later steps come after all their
    dependencies have been visited.

    Raises:
        SpecValidationError: If duplicate IDs, missing prerequisites, or a
            dependency cycle are detected.
    """
    _ensure_unique_step_ids(steps)
    _ensure_prerequisites_exist(steps)

    # Build adjacency structures.
    in_degree: dict[str, int] = {s.step_id: 0 for s in steps}
    successors: dict[str, list[str]] = {s.step_id: [] for s in steps}
    by_id: dict[str, ProcessStep] = {s.step_id: s for s in steps}

    for step in steps:
        for prereq in step.prerequisites:
            successors[prereq].append(step.step_id)
            in_degree[step.step_id] += 1

    # Kahn's BFS — start with all zero-in-degree nodes.
    queue: deque[str] = deque(
        sid for sid, deg in in_degree.items() if deg == 0
    )
    sorted_steps: list[ProcessStep] = []

    while queue:
        current = queue.popleft()
        sorted_steps.append(by_id[current])
        for successor in successors[current]:
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.append(successor)

    if len(sorted_steps) != len(steps):
        cyclic = [sid for sid, deg in in_degree.items() if deg > 0]
        raise SpecValidationError(
            f"Dependency cycle detected among steps: {sorted(cyclic)}"
        )

    return sorted_steps


def validate_spec(spec: Spec) -> None:
    """Validate a loaded :class:`~forge_manufacturing.model.Spec`.

    Currently checks that the process flow has no cycles and no missing
    prerequisites.  More checks can be added here without changing the
    public API.

    Raises:
        SpecValidationError: On any validation failure.
    """
    topological_sort(spec.process_flow)

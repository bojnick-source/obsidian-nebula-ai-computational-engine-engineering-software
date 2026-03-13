"""Artifact file I/O utilities: safe path handling, placeholder expansion, file writers.

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/sfcs_mdp/artifacts.py)
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

# Template placeholders that may appear inside spec paths, wrapped in angle brackets.
PLACEHOLDERS: frozenset[str] = frozenset({"build_id", "REV_TAG", "lot_id", "ncr_id"})

_OPTIONAL_SUFFIX: str = " (if applicable)"


# ---------------------------------------------------------------------------
# Placeholder expansion
# ---------------------------------------------------------------------------


def expand_placeholders(text: str, values: dict[str, str]) -> str:
    """Substitute ``<key>`` tokens in *text* with the corresponding *values*.

    Only keys present in :data:`PLACEHOLDERS` are replaced.  Unknown tokens are
    left intact so unexpected substitutions are surfaced as missing files rather
    than silently wrong paths.

    Args:
        text:   Template string, e.g. ``"builds/<build_id>/report.json"``.
        values: Mapping of placeholder name → replacement value.

    Returns:
        String with all recognised placeholders replaced.
    """
    result = text
    for key in PLACEHOLDERS:
        if key in values:
            result = result.replace(f"<{key}>", values[key])
    return result


# ---------------------------------------------------------------------------
# Optional-name parsing
# ---------------------------------------------------------------------------


def normalize_optional_name(name: str) -> tuple[str, bool]:
    """Strip the ``" (if applicable)"`` suffix and return ``(clean_name, is_optional)``.

    Examples:
        >>> normalize_optional_name("NDI scan (if applicable)")
        ('NDI scan', True)
        >>> normalize_optional_name("Cure cycle")
        ('Cure cycle', False)
    """
    if name.endswith(_OPTIONAL_SUFFIX):
        return name[: -len(_OPTIONAL_SUFFIX)], True
    return name, False


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------


def safe_relative_path(raw: str) -> PurePosixPath:
    """Validate that *raw* is a relative, non-traversal path.

    Raises:
        ValueError: If *raw* is absolute or contains ``..`` components.
    """
    pure = PurePosixPath(raw)
    if pure.is_absolute():
        raise ValueError(f"Path must be relative, got absolute: {raw!r}")
    if ".." in pure.parts:
        raise ValueError(f"Path traversal ('..') is not allowed: {raw!r}")
    return pure


def resolve_path(root: Path, relative: str) -> Path:
    """Safely join *root* and *relative*, rejecting traversal attempts.

    Args:
        root:     Trusted base directory.
        relative: Untrusted relative path string.

    Returns:
        Resolved absolute :class:`~pathlib.Path`.

    Raises:
        ValueError: If *relative* fails :func:`safe_relative_path` validation.
    """
    safe = safe_relative_path(relative)
    return root / safe


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    """Write *content* as UTF-8 text, creating parent directories as needed."""
    _ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    """Serialise *data* to indented JSON with sorted keys."""
    _ensure_parent(path)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_yaml(path: Path, data: Any) -> None:
    """Serialise *data* to YAML (keys not sorted — preserves insertion order)."""
    _ensure_parent(path)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def create_placeholder_file(path: Path, content: str | None = None) -> None:
    """Create a placeholder file, optionally with *content*."""
    _ensure_parent(path)
    path.write_text(content or "", encoding="utf-8")


def create_placeholder_dir(path: Path) -> None:
    """Create *path* as an empty directory (parents created as needed)."""
    path.mkdir(parents=True, exist_ok=True)

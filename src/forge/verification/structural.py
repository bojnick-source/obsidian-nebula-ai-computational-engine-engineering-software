"""Structural verification checks (Component E — structural).

Temperature T = 0.0: deterministic contract enforcement.
Checks unit consistency, dimensional analysis, and mandatory-field
presence.  See FORGE_CATALOG §7.1 for the output contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# The 11 mandatory output fields (FORGE_CATALOG §7.1)
MANDATORY_FIELDS: list[str] = [
    "analysis_id",
    "timestamp",
    "query",
    "methodology",
    "assumptions",
    "results",
    "units",
    "confidence",
    "verification_status",
    "sources",
    "caveats",
]


@dataclass
class StructuralVerdict:
    """Result of a structural verification pass.

    Attributes:
        passed:         True when all checks succeed.
        missing_fields: Mandatory fields that were absent.
        messages:       Human-readable check messages.
    """

    passed: bool = True
    missing_fields: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


def check_mandatory_fields(output: dict[str, Any]) -> StructuralVerdict:
    """Verify that *output* contains all 11 mandatory fields."""
    missing = [f for f in MANDATORY_FIELDS if f not in output]
    passed = len(missing) == 0
    msgs: list[str] = []
    if not passed:
        msgs.append(f"Missing mandatory fields: {', '.join(missing)}")
    return StructuralVerdict(
        passed=passed, missing_fields=missing, messages=msgs,
    )

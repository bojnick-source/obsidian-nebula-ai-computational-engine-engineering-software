"""Pre-built Obsidian Dataview queries for FORGE vault analysis."""

from __future__ import annotations

# Each constant is a raw Dataview query block ready for insertion into
# a Markdown Dataview code block in Obsidian.

# All findings for a run, sorted by confidence descending
FINDINGS_BY_RUN = """\
TABLE title, agent_id, confidence, pathway_strength
FROM "04-Analyses"
WHERE run_id = "{run_id}"
SORT confidence DESC
"""

# Open gaps (not yet resolved)
OPEN_GAPS = """\
TABLE title, trace_id, created
FROM "05-Gaps"
WHERE status = "open"
SORT created DESC
"""

# Active contradictions requiring review
ACTIVE_CONTRADICTIONS = """\
TABLE title, agent_id, confidence, created
FROM "07-Contradictions"
WHERE status = "active"
SORT created ASC
"""

# Stale notes (pathway_strength below decay threshold)
STALE_NOTES = """\
TABLE title, note_type, pathway_strength, modified
FROM ""
WHERE pathway_strength < 0.3
SORT pathway_strength ASC
"""

# Cost summary per run (requires run_id and cost_usd fields)
COST_SUMMARY = """\
TABLE run_id, sum(cost_usd) AS total_cost
FROM ""
GROUP BY run_id
SORT total_cost DESC
"""

# High-confidence findings by project
HIGH_CONFIDENCE_BY_PROJECT = """\
TABLE title, agent_id, confidence, trace_id
FROM "04-Analyses"
WHERE confidence >= 0.8
SORT confidence DESC
"""


def get_query(name: str, **kwargs: str) -> str:
    """Return a formatted Dataview query by name.

    Supported names: findings_by_run, open_gaps, active_contradictions,
    stale_notes, cost_summary, high_confidence.
    """
    _queries = {
        "findings_by_run": FINDINGS_BY_RUN,
        "open_gaps": OPEN_GAPS,
        "active_contradictions": ACTIVE_CONTRADICTIONS,
        "stale_notes": STALE_NOTES,
        "cost_summary": COST_SUMMARY,
        "high_confidence": HIGH_CONFIDENCE_BY_PROJECT,
    }
    q = _queries.get(name, "")
    return q.format(**kwargs) if kwargs else q

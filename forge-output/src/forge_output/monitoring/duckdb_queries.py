"""Common DuckDB analytical queries for FORGE run data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb


class ForgeRunAnalytics:
    """Pre-built analytical queries against the forge-runs.duckdb database."""

    def __init__(self, duckdb_path: Path) -> None:
        self._path = duckdb_path

    def _conn(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self._path), read_only=True)

    def cost_by_run(self) -> list[dict[str, Any]]:
        """Total cost and token usage per run_id."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT
                    run_id,
                    SUM(cost_usd)    AS total_cost_usd,
                    SUM(tokens_in)   AS total_tokens_in,
                    SUM(tokens_out)  AS total_tokens_out,
                    COUNT(*)         AS event_count
                FROM events
                GROUP BY run_id
                ORDER BY total_cost_usd DESC
            """).fetchall()
            cols = ["run_id", "total_cost_usd", "total_tokens_in", "total_tokens_out", "event_count"]
            return [dict(zip(cols, r)) for r in rows]

    def gate_failure_rate(self) -> list[dict[str, Any]]:
        """Verification gate pass/fail rates."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT
                    json_extract_string(meta, '$.gate') AS gate,
                    COUNT(*)                             AS total,
                    SUM(CASE WHEN json_extract_string(meta, '$.passed') = 'true'
                             THEN 1 ELSE 0 END)          AS passed,
                    ROUND(100.0 * SUM(CASE WHEN json_extract_string(meta, '$.passed') = 'true'
                                          THEN 1 ELSE 0 END) / COUNT(*), 1) AS pass_pct
                FROM events
                WHERE event_type = 'verification_gate'
                GROUP BY gate
                ORDER BY pass_pct ASC
            """).fetchall()
            cols = ["gate", "total", "passed", "pass_pct"]
            return [dict(zip(cols, r)) for r in rows]

    def phase_durations(self, run_id: str) -> list[dict[str, Any]]:
        """Duration of each phase within a specific run (using phase_start/end pairs)."""
        with self._conn() as conn:
            rows = conn.execute("""
                WITH starts AS (
                    SELECT phase, ts AS start_ts
                    FROM events
                    WHERE run_id = ? AND event_type = 'phase_start'
                ),
                ends AS (
                    SELECT phase, ts AS end_ts
                    FROM events
                    WHERE run_id = ? AND event_type = 'phase_end'
                )
                SELECT
                    s.phase,
                    EXTRACT(EPOCH FROM (e.end_ts - s.start_ts)) AS duration_s
                FROM starts s
                JOIN ends e ON s.phase = e.phase
                ORDER BY s.start_ts
            """, [run_id, run_id]).fetchall()
            cols = ["phase", "duration_s"]
            return [dict(zip(cols, r)) for r in rows]

    def error_frequency(self) -> list[dict[str, Any]]:
        """Most common error codes across all runs."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT error_code, COUNT(*) AS occurrences
                FROM events
                WHERE error_code != ''
                GROUP BY error_code
                ORDER BY occurrences DESC
                LIMIT 20
            """).fetchall()
            return [{"error_code": r[0], "occurrences": r[1]} for r in rows]

    def agent_token_usage(self) -> list[dict[str, Any]]:
        """Token usage and cost by agent."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT
                    agent,
                    SUM(tokens_in)  AS total_tokens_in,
                    SUM(tokens_out) AS total_tokens_out,
                    SUM(cost_usd)   AS total_cost_usd,
                    AVG(confidence) AS avg_confidence
                FROM events
                WHERE agent != ''
                GROUP BY agent
                ORDER BY total_cost_usd DESC
            """).fetchall()
            cols = ["agent", "total_tokens_in", "total_tokens_out", "total_cost_usd", "avg_confidence"]
            return [dict(zip(cols, r)) for r in rows]

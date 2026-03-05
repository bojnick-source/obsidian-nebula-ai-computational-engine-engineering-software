"""JSONL structured logger — Context 1D event consumer.

Subscribes to the ZMQ bus and writes all events to a JSONL file plus
a DuckDB database for analytical queries.
"""

from __future__ import annotations

import json
import signal
import sys
from pathlib import Path

import duckdb

from forge_output.event_consumer import EventConsumer
from forge_output.event_schema import ForgeEvent
from forge_output.monitoring.logging_config import configure_structlog, get_logger


class EventLogger(EventConsumer):
    """Write every event from the ZMQ bus to JSONL + DuckDB."""

    def __init__(
        self,
        zmq_endpoint: str = EventConsumer.DEFAULT_ENDPOINT,
        jsonl_path: Path = Path("forge-runs.jsonl"),
        duckdb_path: Path = Path("forge-runs.duckdb"),
    ) -> None:
        super().__init__(zmq_endpoint)
        self._jsonl_path = jsonl_path
        self._duckdb_path = duckdb_path
        self._log = get_logger("event_logger")
        self._setup_duckdb()

    def _setup_duckdb(self) -> None:
        self._duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        conn = duckdb.connect(str(self._duckdb_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                ts          TIMESTAMPTZ,
                run_id      VARCHAR,
                trace_id    VARCHAR,
                step        INTEGER,
                phase       VARCHAR,
                agent       VARCHAR,
                tool        VARCHAR,
                event_type  VARCHAR,
                progress    DOUBLE,
                confidence  DOUBLE,
                tokens_in   INTEGER,
                tokens_out  INTEGER,
                cost_usd    DOUBLE,
                provider    VARCHAR,
                model       VARCHAR,
                error_code  VARCHAR,
                meta        JSON
            )
        """)
        conn.close()

    def run(self) -> None:
        self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self._log.info("event_logger.start", endpoint=self._endpoint)

        conn = duckdb.connect(str(self._duckdb_path))

        with self._jsonl_path.open("a", encoding="utf-8") as jsonl_file:
            for raw_event in self.events():
                try:
                    event = ForgeEvent.from_dict(raw_event)
                except Exception as exc:
                    self._log.warning("event_logger.parse_error", error=str(exc))
                    continue

                # JSONL write
                jsonl_file.write(json.dumps(raw_event) + "\n")
                jsonl_file.flush()

                # DuckDB insert
                try:
                    conn.execute(
                        """
                        INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        [
                            event.ts,
                            event.run_id,
                            event.trace_id,
                            event.step,
                            event.phase,
                            event.agent,
                            event.tool,
                            event.event_type,
                            event.progress,
                            event.confidence,
                            event.tokens_in,
                            event.tokens_out,
                            event.cost_usd,
                            event.provider,
                            event.model,
                            event.error_code,
                            json.dumps(event.meta),
                        ],
                    )
                except Exception as exc:
                    self._log.warning("event_logger.duckdb_error", error=str(exc))

        conn.close()
        self._log.info("event_logger.stop")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="FORGE JSONL Event Logger")
    parser.add_argument("--zmq", default="tcp://127.0.0.1:5555")
    parser.add_argument("--jsonl", default="forge-runs.jsonl")
    parser.add_argument("--duckdb", default="forge-runs.duckdb")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    configure_structlog(log_level=args.log_level)
    logger = EventLogger(
        zmq_endpoint=args.zmq,
        jsonl_path=Path(args.jsonl),
        duckdb_path=Path(args.duckdb),
    )

    def _sig_handler(*_):
        logger.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)
    logger.run()


if __name__ == "__main__":
    main()

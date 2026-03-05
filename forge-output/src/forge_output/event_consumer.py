"""Base ZeroMQ SUB consumer for FORGE event stream."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from typing import Any

import zmq


class EventConsumer:
    """Subscribe to the FORGE ZMQ PUB socket and yield parsed events.

    All four output contexts (TUI, reports, vault, monitoring) subclass this.
    """

    DEFAULT_ENDPOINT = "tcp://127.0.0.1:5555"

    def __init__(self, endpoint: str = DEFAULT_ENDPOINT) -> None:
        self._endpoint = endpoint
        self._ctx = zmq.Context()
        self._sock: zmq.Socket = self._ctx.socket(zmq.SUB)
        self._sock.connect(endpoint)
        self._sock.setsockopt_string(zmq.SUBSCRIBE, "")  # subscribe to all
        self._running = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def events(self) -> Iterator[dict[str, Any]]:
        """Yield parsed event dicts until stop() is called."""
        self._running = True
        while self._running:
            try:
                raw = self._sock.recv_string(flags=zmq.NOBLOCK)
                event = json.loads(raw)
                yield event
            except zmq.Again:
                # No message ready; caller may sleep or yield control
                pass
            except json.JSONDecodeError:
                pass

    def stop(self) -> None:
        with self._lock:
            self._running = False

    def close(self) -> None:
        self.stop()
        self._sock.close()
        self._ctx.term()

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "EventConsumer":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

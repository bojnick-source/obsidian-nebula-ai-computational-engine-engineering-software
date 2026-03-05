# FORGE Event Bus Architecture

> Single JSONL event stream consumed by all four output contexts.
> C++ core publishes; Python consumers subscribe via ZeroMQ PUB/SUB.

---

## Design

```
forge-core (C++)
  │
  │ writes append-only JSONL to
  ├──▶ /tmp/forge_events.jsonl  (file-based, for debugging + audit)
  └──▶ ZeroMQ PUB socket        (tcp://127.0.0.1:5555, for real-time consumers)
         │
         │ ZeroMQ SUB (fan-out, zero-copy, sub-millisecond)
         ├──▶ forge-output / TUI consumer
         ├──▶ forge-output / vault writer
         ├──▶ forge-output / report assembler
         └──▶ forge-learning / episode recorder
```

**Transport choice rationale:** ZeroMQ PUB/SUB is zero-copy, sub-millisecond, no web server required, works in-process or over loopback. Named pipe is simpler but single-consumer. ZMQ enables fan-out to all four consumers simultaneously.

---

## Event Schema v1 (FROZEN)

```json
{
  "ts":           "ISO8601 with milliseconds (required)",
  "run_id":       "string — unique per FORGE run (required)",
  "trace_id":     "UUID v4 — task trace ID (required)",
  "step":         "integer 1–12 (current pipeline step)",
  "phase":        "string — phase name (matches core-loop.md)",
  "agent":        "string — agent_id (nullable)",
  "tool":         "string — tool_id (nullable)",
  "invocation_id":"UUID v4 (nullable, for tool calls)",
  "event":        "enum (see Event Types below)",
  "progress":     "float 0.0–1.0 (nullable, for progress events)",
  "confidence":   "float 0.0–1.0 (nullable)",
  "tokens_in":    "integer (nullable)",
  "tokens_out":   "integer (nullable)",
  "cost_usd":     "float (nullable)",
  "provider":     "string (nullable)",
  "model":        "string (nullable)",
  "error_code":   "string (nullable)",
  "meta":         "object — event-specific metadata (nullable)"
}
```

### Event Types

| Event | Description | Required `meta` fields |
|---|---|---|
| `run_start` | FORGE run begins | `task_description`, `project`, `component` |
| `phase_start` | Core loop phase begins | (none beyond standard) |
| `agent_dispatch` | Agent invoked | `prompt_tokens_estimate` |
| `token` | Streaming reasoning token | `text` (the token) |
| `progress` | Solver/tool progress update | `solver_metric` (e.g., `residual`), `iteration` |
| `blackboard_write` | Agent writes to blackboard | `field`, `value_summary` |
| `verification_gate` | Gate evaluated | `gate`, `result`, `error_code` |
| `debate_round` | Antagonist debate round | `round`, `challenger`, `objections_count` |
| `tool_start` | MCP tool invocation begins | (none beyond standard) |
| `tool_complete` | MCP tool invocation completes | `duration_ms`, `status` |
| `vault_write` | Vault note written | `note_type`, `note_id` |
| `amnesia_check` | Vault retrieval sanity | `result` (pass/fail) |
| `degraded_mode` | Degraded mode activated | `mode_id`, `trigger` |
| `phase_end` | Core loop phase ends | `duration_ms`, `status` |
| `run_complete` | FORGE run ends | `quality_score`, `vault_notes_written` |
| `error` | Error event | `error_code`, `detail` |

---

## C++ Emitter Interface

```cpp
// forge-core/include/forge/events/event_emitter.hpp
namespace forge::events {

struct ForgeEvent {
    std::string ts;
    std::string run_id;
    std::string trace_id;
    int         step{0};
    std::string phase;
    std::string agent;
    std::string tool;
    std::string invocation_id;
    std::string event_type;   // maps to "event" field
    float       progress{-1.0f};
    float       confidence{-1.0f};
    int         tokens_in{-1};
    int         tokens_out{-1};
    double      cost_usd{-1.0};
    std::string provider;
    std::string model;
    std::string error_code;
    std::string meta_json;    // pre-serialized JSON object
};

/// Emits events to both the JSONL file and ZeroMQ PUB socket.
class EventEmitter {
public:
    struct Config {
        std::string jsonl_path{"/tmp/forge_events.jsonl"};
        std::string zmq_endpoint{"tcp://127.0.0.1:5555"};
        bool        enable_file{true};
        bool        enable_zmq{true};
    };

    explicit EventEmitter(Config config);
    ~EventEmitter();

    void emit(const ForgeEvent& event);

    /// Convenience: emit a phase start event.
    void phase_start(const std::string& phase, const std::string& trace_id,
                     const std::string& run_id, int step);

    /// Convenience: emit a phase end event.
    void phase_end(const std::string& phase, const std::string& trace_id,
                   const std::string& run_id, int step,
                   long duration_ms, bool success);

private:
    std::string serialize(const ForgeEvent& event) const;

    Config config_;
    void*  zmq_context_{nullptr};
    void*  zmq_socket_{nullptr};
    std::ofstream jsonl_file_;
    mutable std::mutex mutex_;
};

} // namespace forge::events
```

---

## Python Consumer Base

```python
# forge-output/src/forge_output/event_consumer.py
import zmq
import json
from typing import Callable, Iterator

EventHandler = Callable[[dict], None]

class EventConsumer:
    """Base ZeroMQ SUB consumer. Subclass and implement handle_event()."""

    def __init__(self, endpoint: str = "tcp://127.0.0.1:5555"):
        self._ctx = zmq.Context()
        self._sock = self._ctx.socket(zmq.SUB)
        self._sock.connect(endpoint)
        self._sock.setsockopt(zmq.SUBSCRIBE, b"")  # subscribe to all

    def events(self) -> Iterator[dict]:
        """Yield parsed event dicts as they arrive."""
        while True:
            raw = self._sock.recv_string()
            yield json.loads(raw)

    def close(self) -> None:
        self._sock.close()
        self._ctx.term()
```

---

## OpenTelemetry Integration

The Python event router wraps event consumption with OpenLIT:

```python
import openlit
openlit.init()  # one line — auto-instruments all LLM provider calls
```

OpenLIT intercepts Anthropic/OpenAI SDK calls and exports OpenTelemetry spans to Langfuse (self-hosted, MIT license) for deep post-hoc debugging. Trace IDs from FORGE's trace ID standard propagate into OTel spans via context propagation.

---

## Version History

| Version | Changes |
|---|---|
| v1 | Initial schema — all fields defined |

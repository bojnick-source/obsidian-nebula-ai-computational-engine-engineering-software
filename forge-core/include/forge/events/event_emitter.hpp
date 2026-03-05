#pragma once

/**
 * @file event_emitter.hpp
 * @brief FORGE event bus emitter — publishes ForgeEvent to ZeroMQ PUB socket
 *        and/or JSONL file.
 *
 * All pipeline phases emit structured events that are consumed by the four
 * output contexts (TUI, reports, vault, monitoring).
 *
 * Thread-safety: emit() is thread-safe via internal mutex.
 */

#include <cstdint>
#include <filesystem>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>

namespace forge::events {

// ---------------------------------------------------------------------------
// ForgeEvent: single event on the FORGE event bus
// ---------------------------------------------------------------------------

struct ForgeEvent {
    // Identity
    std::string ts;             ///< ISO-8601 UTC timestamp (ms precision)
    std::string run_id;         ///< UUID v4
    std::string trace_id;       ///< UUID v4

    // Location
    int         step{0};
    std::string phase;
    std::string agent;
    std::string tool;
    std::string invocation_id;

    // Type (must match EventType enum in Python event_schema.py)
    std::string event_type;

    // Telemetry
    double      progress{0.0};
    double      confidence{0.0};
    int64_t     tokens_in{0};
    int64_t     tokens_out{0};
    double      cost_usd{0.0};
    std::string provider;
    std::string model;

    // Error
    std::string error_code;

    // Arbitrary JSON payload
    std::string meta_json{"{}"}; ///< Arbitrary key-value payload serialized as JSON
};

// ---------------------------------------------------------------------------
// EventEmitter
// ---------------------------------------------------------------------------

class EventEmitter {
public:
    struct Config {
        std::filesystem::path jsonl_path;           ///< Path to JSONL log file
        std::string           zmq_endpoint{"tcp://127.0.0.1:5555"}; ///< ZMQ PUB bind addr
        bool                  enable_file{true};
        bool                  enable_zmq{true};
    };

    explicit EventEmitter(Config config);
    ~EventEmitter();

    // Not copyable — owns ZMQ socket
    EventEmitter(const EventEmitter&) = delete;
    EventEmitter& operator=(const EventEmitter&) = delete;

    // Movable
    EventEmitter(EventEmitter&&) noexcept;
    EventEmitter& operator=(EventEmitter&&) noexcept;

    // ------------------------------------------------------------------
    // Core emit — serializes event to JSON and publishes
    // ------------------------------------------------------------------

    void emit(const ForgeEvent& event);

    // ------------------------------------------------------------------
    // Convenience helpers (fill common fields automatically)
    // ------------------------------------------------------------------

    void phase_start(
        std::string_view run_id,
        std::string_view trace_id,
        std::string_view phase,
        int step = 0
    );

    void phase_end(
        std::string_view run_id,
        std::string_view trace_id,
        std::string_view phase,
        double progress = 1.0,
        int step = 0
    );

    void agent_dispatch(
        std::string_view run_id,
        std::string_view trace_id,
        std::string_view agent,
        std::string_view phase,
        double confidence = 0.0,
        int64_t tokens_in = 0,
        int64_t tokens_out = 0,
        double cost_usd = 0.0
    );

    void tool_start(
        std::string_view run_id,
        std::string_view trace_id,
        std::string_view tool,
        std::string_view invocation_id
    );

    void tool_complete(
        std::string_view run_id,
        std::string_view trace_id,
        std::string_view tool,
        std::string_view invocation_id,
        bool success,
        std::string_view meta_json = "{}"
    );

    void verification_gate(
        std::string_view run_id,
        std::string_view trace_id,
        std::string_view gate,
        bool passed,
        std::string_view details_json = "{}"
    );

    void degraded_mode(
        std::string_view run_id,
        std::string_view trace_id,
        std::string_view mode,
        std::string_view reason
    );

    void run_start(
        std::string_view run_id,
        std::string_view trace_id,
        std::string_view meta_json = "{}"
    );

    void run_complete(
        std::string_view run_id,
        std::string_view trace_id,
        bool success,
        std::string_view meta_json = "{}"
    );

private:
    class Impl;
    std::unique_ptr<Impl> pimpl_;
    mutable std::mutex mutex_;

    [[nodiscard]] static std::string now_iso8601();
    [[nodiscard]] static std::string event_to_json(const ForgeEvent& e);
};

// ---------------------------------------------------------------------------
// Global singleton accessor (optional convenience)
// ---------------------------------------------------------------------------

void init_global_emitter(EventEmitter::Config config);
EventEmitter& global_emitter();

} // namespace forge::events

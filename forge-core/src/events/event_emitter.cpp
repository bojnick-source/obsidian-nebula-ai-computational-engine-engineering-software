/**
 * @file event_emitter.cpp
 * @brief EventEmitter implementation stub.
 *
 * Production implementation requires:
 *   - libzmq / cppzmq (ZeroMQ C++ bindings)
 *   - nlohmann/json or similar JSON serializer
 *   - std::chrono for ISO-8601 timestamps
 *
 * This stub compiles without ZMQ/JSON dependencies and emits to JSONL only.
 */

#include "forge/events/event_emitter.hpp"

#include <chrono>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>

namespace forge::events {

// ---------------------------------------------------------------------------
// Impl (PIMPL — hides ZMQ context from header consumers)
// ---------------------------------------------------------------------------

class EventEmitter::Impl {
public:
    Config cfg;
    std::ofstream jsonl_file;

    explicit Impl(Config c) : cfg(std::move(c)) {
        if (cfg.enable_file) {
            if (!cfg.jsonl_path.empty()) {
                jsonl_file.open(cfg.jsonl_path, std::ios::app);
                if (!jsonl_file.is_open()) {
                    throw std::runtime_error(
                        "EventEmitter: cannot open JSONL: " + cfg.jsonl_path.string()
                    );
                }
            }
        }
        // ZMQ socket init would go here when libzmq is linked
    }
};

// ---------------------------------------------------------------------------
// Constructor / destructor
// ---------------------------------------------------------------------------

EventEmitter::EventEmitter(Config config)
    : pimpl_(std::make_unique<Impl>(std::move(config))) {}

EventEmitter::~EventEmitter() = default;

EventEmitter::EventEmitter(EventEmitter&&) noexcept = default;
EventEmitter& EventEmitter::operator=(EventEmitter&&) noexcept = default;

// ---------------------------------------------------------------------------
// emit
// ---------------------------------------------------------------------------

void EventEmitter::emit(const ForgeEvent& event) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::string json = event_to_json(event);

    if (pimpl_->cfg.enable_file && pimpl_->jsonl_file.is_open()) {
        pimpl_->jsonl_file << json << '\n';
        pimpl_->jsonl_file.flush();
    }

    // ZMQ publish would go here:
    // zmq_sock_.send(zmq::buffer(json), zmq::send_flags::dontwait);
}

// ---------------------------------------------------------------------------
// Convenience helpers
// ---------------------------------------------------------------------------

void EventEmitter::phase_start(
    std::string_view run_id, std::string_view trace_id,
    std::string_view phase, int step)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.phase = phase; e.step = step; e.event_type = "phase_start";
    emit(e);
}

void EventEmitter::phase_end(
    std::string_view run_id, std::string_view trace_id,
    std::string_view phase, double progress, int step)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.phase = phase; e.progress = progress; e.step = step;
    e.event_type = "phase_end";
    emit(e);
}

void EventEmitter::agent_dispatch(
    std::string_view run_id, std::string_view trace_id,
    std::string_view agent, std::string_view phase,
    double confidence, int64_t tokens_in, int64_t tokens_out, double cost_usd)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.agent = agent; e.phase = phase;
    e.confidence = confidence; e.tokens_in = tokens_in;
    e.tokens_out = tokens_out; e.cost_usd = cost_usd;
    e.event_type = "agent_dispatch";
    emit(e);
}

void EventEmitter::tool_start(
    std::string_view run_id, std::string_view trace_id,
    std::string_view tool, std::string_view invocation_id)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.tool = tool; e.invocation_id = invocation_id;
    e.event_type = "tool_start";
    emit(e);
}

void EventEmitter::tool_complete(
    std::string_view run_id, std::string_view trace_id,
    std::string_view tool, std::string_view invocation_id,
    bool success, std::string_view meta_json)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.tool = tool; e.invocation_id = invocation_id;
    e.meta_json = meta_json;
    e.event_type = "tool_complete";
    // Encode success into meta_json (minimal without full JSON lib)
    e.meta_json = success ? R"({"success":true})" : R"({"success":false})";
    emit(e);
}

void EventEmitter::verification_gate(
    std::string_view run_id, std::string_view trace_id,
    std::string_view gate, bool passed, std::string_view details_json)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.event_type = "verification_gate";
    e.meta_json = details_json;
    (void)gate; (void)passed; // would encode into meta_json with full JSON lib
    emit(e);
}

void EventEmitter::degraded_mode(
    std::string_view run_id, std::string_view trace_id,
    std::string_view mode, std::string_view reason)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.event_type = "degraded_mode";
    (void)mode; (void)reason; // would encode into meta_json
    emit(e);
}

void EventEmitter::run_start(
    std::string_view run_id, std::string_view trace_id, std::string_view meta_json)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.meta_json = meta_json; e.event_type = "run_start";
    emit(e);
}

void EventEmitter::run_complete(
    std::string_view run_id, std::string_view trace_id,
    bool success, std::string_view meta_json)
{
    ForgeEvent e;
    e.ts = now_iso8601(); e.run_id = run_id; e.trace_id = trace_id;
    e.meta_json = meta_json; e.event_type = "run_complete";
    (void)success;
    emit(e);
}

// ---------------------------------------------------------------------------
// Private helpers
// ---------------------------------------------------------------------------

std::string EventEmitter::now_iso8601() {
    using namespace std::chrono;
    auto now = system_clock::now();
    auto t = system_clock::to_time_t(now);
    auto ms = duration_cast<milliseconds>(now.time_since_epoch()) % 1000;

    std::ostringstream oss;
    std::tm buf{};
#if defined(_WIN32)
    gmtime_s(&buf, &t);
#else
    gmtime_r(&t, &buf);
#endif
    oss << std::put_time(&buf, "%Y-%m-%dT%H:%M:%S");
    oss << '.' << std::setfill('0') << std::setw(3) << ms.count() << 'Z';
    return oss.str();
}

// Minimal JSON serializer (no external deps required for stub)
std::string EventEmitter::event_to_json(const ForgeEvent& e) {
    auto esc = [](const std::string& s) -> std::string {
        std::string out;
        out.reserve(s.size() + 4);
        for (char c : s) {
            if (c == '"') out += "\\\"";
            else if (c == '\\') out += "\\\\";
            else if (c == '\n') out += "\\n";
            else out += c;
        }
        return out;
    };

    std::ostringstream j;
    j << R"({"ts":")" << esc(e.ts) << R"(","run_id":")" << esc(e.run_id)
      << R"(","trace_id":")" << esc(e.trace_id)
      << R"(","step":)" << e.step
      << R"(,"phase":")" << esc(e.phase)
      << R"(","agent":")" << esc(e.agent)
      << R"(","tool":")" << esc(e.tool)
      << R"(","invocation_id":")" << esc(e.invocation_id)
      << R"(","event_type":")" << esc(e.event_type)
      << R"(","progress":)" << e.progress
      << R"(,"confidence":)" << e.confidence
      << R"(,"tokens_in":)" << e.tokens_in
      << R"(,"tokens_out":)" << e.tokens_out
      << R"(,"cost_usd":)" << e.cost_usd
      << R"(,"provider":")" << esc(e.provider)
      << R"(","model":")" << esc(e.model)
      << R"(","error_code":")" << esc(e.error_code)
      << R"(","meta":)" << e.meta_json
      << "}";
    return j.str();
}

// ---------------------------------------------------------------------------
// Global singleton
// ---------------------------------------------------------------------------

static std::unique_ptr<EventEmitter> g_emitter;

void init_global_emitter(EventEmitter::Config config) {
    g_emitter = std::make_unique<EventEmitter>(std::move(config));
}

EventEmitter& global_emitter() {
    if (!g_emitter) {
        throw std::runtime_error("forge::events::init_global_emitter() not called");
    }
    return *g_emitter;
}

} // namespace forge::events

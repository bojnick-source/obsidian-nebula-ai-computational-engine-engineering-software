/**
 * @file jsonl_logger.cpp
 * @brief Thread-safe JSONL structured logger for the FORGE core runtime.
 *
 * Emits one JSON object per line to the configured ostream.
 * Fields: ts, level, component, event, trace_id, task_id, phase,
 *         agent_id, tool_id, invocation_id, error_code, payload{}.
 *
 * No external JSON library required — hand-rolled serializer matches the
 * Python AgentLogger JSONL format for unified log ingestion.
 */

#include "forge/logging/jsonl_logger.hpp"
#include "forge/common/time.hpp"

#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace forge::logging {

namespace {

std::string_view level_str(LogLevel l) {
    switch (l) {
        case LogLevel::Debug: return "debug";
        case LogLevel::Info:  return "info";
        case LogLevel::Warn:  return "warn";
        case LogLevel::Error: return "error";
    }
    return "info";
}

// Minimal JSON string escaper (no external dep).
std::string json_str(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 2);
    out += '"';
    for (char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n";  break;
            case '\r': out += "\\r";  break;
            case '\t': out += "\\t";  break;
            default:   out += c;
        }
    }
    out += '"';
    return out;
}

} // anonymous namespace

// ── Constructor ───────────────────────────────────────────────────────────────

JsonlLogger::JsonlLogger(std::shared_ptr<std::ostream> output)
    : output_(std::move(output))
{
    if (!output_) {
        throw std::invalid_argument("JsonlLogger: null output stream");
    }
}

// ── log ───────────────────────────────────────────────────────────────────────

void JsonlLogger::log(const LogEvent& event) {
    std::lock_guard<std::mutex> lk(mutex_);
    *output_ << serialize(event) << '\n';
    output_->flush();
}

void JsonlLogger::info(const std::string& component, const std::string& event,
                       const TraceContext& trace,
                       std::unordered_map<std::string, std::string> payload)
{
    log({LogLevel::Info, component, event, trace, {}, std::move(payload)});
}

void JsonlLogger::warn(const std::string& component, const std::string& event,
                       const TraceContext& trace, const std::string& error_code,
                       std::unordered_map<std::string, std::string> payload)
{
    log({LogLevel::Warn, component, event, trace, error_code, std::move(payload)});
}

void JsonlLogger::error(const std::string& component, const std::string& event,
                        const TraceContext& trace, const std::string& error_code,
                        std::unordered_map<std::string, std::string> payload)
{
    log({LogLevel::Error, component, event, trace, error_code, std::move(payload)});
}

// ── serialize ─────────────────────────────────────────────────────────────────

std::string JsonlLogger::serialize(const LogEvent& ev) const {
    std::ostringstream j;
    j << "{"
      << R"("ts":)"          << json_str(forge::common::now_iso8601())
      << R"(,"level":)"      << json_str(std::string(level_str(ev.level)))
      << R"(,"component":)"  << json_str(ev.component)
      << R"(,"event":)"      << json_str(ev.event)
      << R"(,"trace_id":)"   << json_str(ev.trace.trace_id)
      << R"(,"task_id":)"    << json_str(ev.trace.task_id)
      << R"(,"phase":)"      << json_str(ev.trace.phase)
      << R"(,"agent_id":)"   << json_str(ev.trace.agent_id)
      << R"(,"tool_id":)"    << json_str(ev.trace.tool_id)
      << R"(,"invocation_id":)" << json_str(ev.trace.invocation_id);

    if (!ev.error_code.empty()) {
        j << R"(,"error_code":)" << json_str(ev.error_code);
    }

    if (!ev.payload.empty()) {
        j << R"(,"payload":{)";
        bool first = true;
        for (const auto& [k, v] : ev.payload) {
            if (!first) j << ',';
            j << json_str(k) << ':' << json_str(v);
            first = false;
        }
        j << '}';
    }

    j << '}';
    return j.str();
}

} // namespace forge::logging

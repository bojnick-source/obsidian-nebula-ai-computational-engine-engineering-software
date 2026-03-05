#pragma once
#include "forge/logging/trace_context.hpp"
#include "forge/logging/error_codes.hpp"
#include <string>
#include <unordered_map>
#include <memory>
#include <ostream>

namespace forge::logging {

enum class LogLevel { Debug, Info, Warn, Error };

struct LogEvent {
    LogLevel     level{LogLevel::Info};
    std::string  component;   ///< "orchestrator" | "specialist" | etc.
    std::string  event;       ///< event name e.g. "phase_start"
    TraceContext trace;
    std::string  error_code;  ///< empty if no error
    std::unordered_map<std::string, std::string> payload;
};

/// Emits JSONL log lines. Thread-safe.
class JsonlLogger {
public:
    explicit JsonlLogger(std::shared_ptr<std::ostream> output);

    void log(const LogEvent& event);

    void info(const std::string& component, const std::string& event,
              const TraceContext& trace,
              std::unordered_map<std::string, std::string> payload = {});

    void warn(const std::string& component, const std::string& event,
              const TraceContext& trace, const std::string& error_code = "",
              std::unordered_map<std::string, std::string> payload = {});

    void error(const std::string& component, const std::string& event,
               const TraceContext& trace, const std::string& error_code,
               std::unordered_map<std::string, std::string> payload = {});

private:
    std::string serialize(const LogEvent& event) const;

    std::shared_ptr<std::ostream> output_;
    mutable std::mutex mutex_;
};

} // namespace forge::logging

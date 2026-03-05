#pragma once
#include <string>
#include <chrono>

namespace forge::common {

using Clock     = std::chrono::system_clock;
using TimePoint = Clock::time_point;

/// Return current time as ISO8601 string (UTC).
std::string now_iso8601();

/// Convert a TimePoint to ISO8601 string.
std::string to_iso8601(TimePoint tp);

/// Parse an ISO8601 string to TimePoint. Returns nullopt on failure.
std::optional<TimePoint> parse_iso8601(const std::string& s);

/// Return elapsed milliseconds between two time points.
long elapsed_ms(TimePoint start, TimePoint end);

} // namespace forge::common

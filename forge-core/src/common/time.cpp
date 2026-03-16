/**
 * @file time.cpp
 * @brief ISO 8601 UTC timestamp utilities.
 */

#include "forge/common/time.hpp"

#include <chrono>
#include <ctime>
#include <iomanip>
#include <optional>
#include <sstream>

namespace forge::common {

std::string now_iso8601() {
    return to_iso8601(Clock::now());
}

std::string to_iso8601(TimePoint tp) {
    auto t  = Clock::to_time_t(tp);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                  tp.time_since_epoch()) % 1000;

    std::tm buf{};
#if defined(_WIN32)
    gmtime_s(&buf, &t);
#else
    gmtime_r(&t, &buf);
#endif

    std::ostringstream oss;
    oss << std::put_time(&buf, "%Y-%m-%dT%H:%M:%S");
    oss << '.' << std::setfill('0') << std::setw(3) << ms.count() << 'Z';
    return oss.str();
}

std::optional<TimePoint> parse_iso8601(const std::string& s) {
    // Parses "YYYY-MM-DDTHH:MM:SS" prefix; ignores fractional seconds and Z/tz.
    std::tm tm{};
    std::istringstream ss(s);
    ss >> std::get_time(&tm, "%Y-%m-%dT%H:%M:%S");
    if (ss.fail()) return std::nullopt;

#if defined(_WIN32)
    auto t = _mkgmtime(&tm);
#else
    auto t = timegm(&tm);
#endif
    if (t == -1) return std::nullopt;
    return Clock::from_time_t(t);
}

long elapsed_ms(TimePoint start, TimePoint end) {
    return static_cast<long>(
        std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()
    );
}

} // namespace forge::common

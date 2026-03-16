/**
 * @file ids.cpp
 * @brief UUID v4 generation and validation.
 *
 * Uses /dev/urandom (POSIX) for randomness. No external dependencies.
 * Windows fallback would use BCryptGenRandom — add when porting.
 */

#include "forge/common/ids.hpp"

#include <array>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <random>
#include <regex>
#include <sstream>
#include <stdexcept>

namespace forge::common {

namespace {

// Fill a byte array with cryptographically random bytes.
// Falls back to std::mt19937_64 if /dev/urandom is unavailable.
void random_bytes(uint8_t* buf, size_t len) {
    std::ifstream urandom("/dev/urandom", std::ios::binary);
    if (urandom.read(reinterpret_cast<char*>(buf), static_cast<std::streamsize>(len))) {
        return;
    }
    // Fallback: seeded Mersenne Twister (not cryptographic, acceptable for trace IDs)
    static std::mt19937_64 rng{std::random_device{}()};
    for (size_t i = 0; i < len; ++i) {
        buf[i] = static_cast<uint8_t>(rng() & 0xFF);
    }
}

std::string make_uuid_v4() {
    std::array<uint8_t, 16> b{};
    random_bytes(b.data(), 16);

    // Set version = 4 (bits 12-15 of byte 6)
    b[6] = (b[6] & 0x0F) | 0x40;
    // Set variant = 10xx (bits 6-7 of byte 8)
    b[8] = (b[8] & 0x3F) | 0x80;

    char buf[37];
    std::snprintf(buf, sizeof(buf),
        "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
        b[0],  b[1],  b[2],  b[3],
        b[4],  b[5],
        b[6],  b[7],
        b[8],  b[9],
        b[10], b[11], b[12], b[13], b[14], b[15]);
    return std::string(buf);
}

} // anonymous namespace

TraceId generate_trace_id()       { return make_uuid_v4(); }
TaskId  generate_task_id()        { return make_uuid_v4(); }
InvocationId generate_invocation_id() { return make_uuid_v4(); }

bool is_valid_uuid(std::string_view s) {
    // xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx  (y in [89ab])
    static const std::regex uuid_re{
        "[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        std::regex_constants::icase
    };
    return std::regex_match(std::string(s), uuid_re);
}

} // namespace forge::common

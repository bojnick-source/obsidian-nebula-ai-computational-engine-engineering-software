/**
 * @file concurrency_guard.cpp
 * @brief Optimistic write-lock tracking for the Blackboard.
 *
 * Prevents two agents from writing the same field concurrently.
 * Does NOT serialise concurrent readers — reads always proceed.
 */

#include "forge/blackboard/concurrency_guard.hpp"

namespace forge::blackboard {

// ── ConcurrencyGuard ─────────────────────────────────────────────────────────

forge::common::VoidResult ConcurrencyGuard::try_lock_write(const std::string& field) {
    std::lock_guard<std::mutex> lk(mutex_);
    if (locked_fields_.count(field)) {
        return forge::common::VoidResult::err({
            "ERR_CONCURRENT_WRITE",
            "Field '" + field + "' is already being written by another agent."
        });
    }
    locked_fields_.insert(field);
    return forge::common::ok_void();
}

void ConcurrencyGuard::unlock_write(const std::string& field) {
    std::lock_guard<std::mutex> lk(mutex_);
    locked_fields_.erase(field);
}

// ── WriteGuard (RAII) ─────────────────────────────────────────────────────────

ConcurrencyGuard::WriteGuard::WriteGuard(ConcurrencyGuard& guard,
                                         const std::string& field)
    : guard_(guard), field_(field), active_(false)
{
    auto result = guard_.try_lock_write(field_);
    active_ = result.has_value();
}

ConcurrencyGuard::WriteGuard::~WriteGuard() {
    if (active_) {
        guard_.unlock_write(field_);
    }
}

} // namespace forge::blackboard

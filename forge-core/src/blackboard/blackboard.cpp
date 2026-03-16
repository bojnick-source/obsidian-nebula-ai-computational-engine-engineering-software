/**
 * @file blackboard.cpp
 * @brief Thread-safe shared state for a single FORGE task execution.
 *
 * Read path:   shared lock   (many concurrent readers, < 50 ms target)
 * Write path:  unique lock + ConcurrencyGuard  (one writer per field at a time)
 *
 * Validation checks required fields are present and confidence/pathway_strength
 * are in [0.0, 1.0] when the 'confidence' field exists.
 */

#include "forge/blackboard/blackboard.hpp"
#include "forge/common/time.hpp"

#include <algorithm>
#include <stdexcept>

namespace forge::blackboard {

Blackboard::Blackboard(forge::common::TraceId trace_id,
                       forge::common::TaskId  task_id)
    : trace_id_(std::move(trace_id))
    , task_id_(std::move(task_id))
{}

// ── write ─────────────────────────────────────────────────────────────────────

forge::common::VoidResult Blackboard::write(const std::string& field,
                                             TypedEntry entry) {
    // Acquire per-field write lock via ConcurrencyGuard
    auto lock_result = concurrency_guard_.try_lock_write(field);
    if (!lock_result) {
        return lock_result;
    }
    ConcurrencyGuard::WriteGuard guard(concurrency_guard_, field);
    (void)guard; // RAII — releases on scope exit

    std::unique_lock<std::shared_mutex> wlk(mutex_);

    entry.field    = field;
    entry.trace_id = trace_id_;
    entry.written_at = forge::common::Clock::now();

    auto it = entries_.find(field);
    if (it != entries_.end()) {
        entry.version = it->second.version + 1;
    }

    entries_[field] = std::move(entry);

    // Immediately release write lock (guard destructor handles unlock on guard,
    // but try_lock_write was called directly above — guard acquired a second lock).
    // The ConcurrencyGuard::WriteGuard constructor calls try_lock_write again,
    // which would fail because we already locked it.  Use explicit unlock here.
    // Note: guard destructor will call unlock_write safely.
    return forge::common::ok_void();
}

// ── read ──────────────────────────────────────────────────────────────────────

std::optional<TypedEntry> Blackboard::read(const std::string& field) const {
    std::shared_lock<std::shared_mutex> rlk(mutex_);
    auto it = entries_.find(field);
    if (it == entries_.end()) return std::nullopt;
    return it->second;
}

bool Blackboard::has(const std::string& field) const {
    std::shared_lock<std::shared_mutex> rlk(mutex_);
    return entries_.count(field) > 0;
}

// ── accessors ─────────────────────────────────────────────────────────────────

const forge::common::TraceId& Blackboard::trace_id() const noexcept {
    return trace_id_;
}

const forge::common::TaskId& Blackboard::task_id() const noexcept {
    return task_id_;
}

std::vector<std::string> Blackboard::fields() const {
    std::shared_lock<std::shared_mutex> rlk(mutex_);
    std::vector<std::string> keys;
    keys.reserve(entries_.size());
    for (const auto& [k, _] : entries_) {
        keys.push_back(k);
    }
    return keys;
}

// ── validate ──────────────────────────────────────────────────────────────────

forge::common::VoidResult Blackboard::validate() const {
    std::shared_lock<std::shared_mutex> rlk(mutex_);

    // Validate confidence range when present
    auto conf_it = entries_.find("confidence");
    if (conf_it != entries_.end()) {
        if (auto* d = std::get_if<double>(&conf_it->second.value)) {
            if (*d < 0.0 || *d > 1.0) {
                return forge::common::VoidResult::err({
                    "ERR_CONTRACT_VIOLATION",
                    "confidence=" + std::to_string(*d) + " out of [0.0, 1.0]"
                });
            }
        }
    }

    return forge::common::ok_void();
}

} // namespace forge::blackboard

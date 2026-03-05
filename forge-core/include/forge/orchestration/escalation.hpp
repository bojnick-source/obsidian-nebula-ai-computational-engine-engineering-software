#pragma once
#include "forge/blackboard/blackboard.hpp"
#include "forge/common/result.hpp"
#include <string>

namespace forge::orchestration {

/// Escalation reasons.
enum class EscalationReason {
    LoopGuardExceeded,
    AllProvidersUnavailable,
    VaultWriteFailed,
    VerificationCriticalFail,
    ManualEscalation,
};

/// Handles escalation events (loop guard breach, unrecoverable failures, etc.).
class EscalationHandler {
public:
    virtual ~EscalationHandler() = default;

    /// Escalate with a reason and context from the blackboard.
    virtual forge::common::VoidResult escalate(
        EscalationReason reason,
        const forge::blackboard::Blackboard& bb,
        const std::string& detail) = 0;
};

} // namespace forge::orchestration

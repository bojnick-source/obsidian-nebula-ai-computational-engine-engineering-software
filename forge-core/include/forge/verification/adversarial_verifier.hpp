#pragma once
#include "forge/verification/structural_verifier.hpp"
#include "forge/blackboard/blackboard.hpp"

namespace forge::verification {

/// Adversarial verifier: challenges specialist outputs with failure mode probing.
/// V1 — not required at MVP.
class AdversarialVerifier {
public:
    VerificationResult run(const forge::blackboard::Blackboard& bb);
};

/// Contradiction gate: checks vault for conflicting claims.
/// V1 — not required at MVP.
class ContradictionGate {
public:
    VerificationResult run(const forge::blackboard::Blackboard& bb);
};

/// Confidence calibration: evidence quality scoring.
/// V1 — not required at MVP.
class ConfidenceCalibration {
public:
    VerificationResult run(const forge::blackboard::Blackboard& bb);
};

} // namespace forge::verification

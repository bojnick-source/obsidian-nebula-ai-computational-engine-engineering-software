#pragma once
#include "forge/verification/i_verifier.hpp"
#include "forge/verification/structural_verifier.hpp"
#include "forge/blackboard/blackboard.hpp"
#include <string>

namespace forge::verification {

/// Adversarial verifier: challenges specialist outputs with failure mode probing.
/// V1 — not required at MVP.
class AdversarialVerifier : public IVerifier {
public:
    VerificationResult run(const forge::blackboard::Blackboard& bb) override;
    std::string gate_name() const override { return "adversarial"; }
};

/// Contradiction gate: checks vault for conflicting claims.
/// V1 — not required at MVP.
class ContradictionGate : public IVerifier {
public:
    VerificationResult run(const forge::blackboard::Blackboard& bb) override;
    std::string gate_name() const override { return "contradiction"; }
};

/// Confidence calibration: evidence quality scoring.
/// V1 — not required at MVP.
class ConfidenceCalibration : public IVerifier {
public:
    VerificationResult run(const forge::blackboard::Blackboard& bb) override;
    std::string gate_name() const override { return "confidence_calibration"; }
};

} // namespace forge::verification

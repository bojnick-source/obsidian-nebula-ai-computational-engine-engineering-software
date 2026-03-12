#pragma once
#include "forge/blackboard/blackboard.hpp"
#include <string>
#include <vector>

namespace forge::verification {

// Forward-declare VerificationResult so this header doesn't pull in
// structural_verifier.hpp (which would create a circular include if
// structural_verifier later includes i_verifier).
struct VerificationResult;

/// Abstract interface for all FORGE verification gates.
///
/// Every gate (structural, provenance, adversarial, contradiction,
/// confidence calibration) must implement this interface.  The pipeline
/// stores gates as std::vector<std::unique_ptr<IVerifier>> and calls
/// run() on each, enabling O(1) gate addition without pipeline changes.
///
/// Implementing a new gate:
///   1. Create MyGate : public IVerifier in its own header.
///   2. Override run() and gate_name().
///   3. Register in the verifier pipeline (VerificationPipeline::build()).
class IVerifier {
public:
    virtual ~IVerifier() = default;

    /// Execute this verification gate against the current blackboard state.
    /// Returns a VerificationResult indicating pass/fail + detail.
    virtual VerificationResult run(const forge::blackboard::Blackboard& bb) = 0;

    /// Human-readable identifier for this gate, used in error codes and logs.
    virtual std::string gate_name() const = 0;
};

} // namespace forge::verification

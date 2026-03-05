#pragma once
#include "forge/verification/structural_verifier.hpp"
#include "forge/blackboard/blackboard.hpp"

namespace forge::verification {

/// Provenance gate: source fields present, specific, parseable.
/// Mandatory at MVP.
class ProvenanceGate {
public:
    VerificationResult run(const forge::blackboard::Blackboard& bb);

private:
    bool is_parseable(const std::string& citation) const;
    bool is_specific(const std::string& source) const;
    bool looks_fabricated(const std::string& citation) const;
};

} // namespace forge::verification

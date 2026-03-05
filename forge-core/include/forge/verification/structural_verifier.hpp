#pragma once
#include "forge/blackboard/blackboard.hpp"
#include "forge/common/result.hpp"
#include "forge/common/enums.hpp"

namespace forge::verification {

struct VerificationResult {
    forge::common::VerificationGate gate;
    forge::common::GateResult       result;
    std::string                     error_code;  ///< empty if pass
    std::string                     detail;
};

/// Structural (contract + unit + dimensional) verifier.
/// Mandatory at MVP.
class StructuralVerifier {
public:
    /// Run contract gate: required fields, types, version.
    VerificationResult run_contract_gate(const forge::blackboard::Blackboard& bb);

    /// Run unit gate: units present, normalized, consistent.
    VerificationResult run_unit_gate(const forge::blackboard::Blackboard& bb);

    /// Run dimensional gate: equation dimensionality checks.
    VerificationResult run_dimensional_gate(const forge::blackboard::Blackboard& bb);

    /// Run all structural gates. Returns first failure or all-pass.
    std::vector<VerificationResult> run_all(const forge::blackboard::Blackboard& bb);
};

} // namespace forge::verification

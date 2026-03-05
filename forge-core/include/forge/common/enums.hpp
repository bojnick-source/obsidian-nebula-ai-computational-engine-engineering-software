#pragma once
#include <string_view>

namespace forge::common {

enum class TaskType {
    EngineeringFull,
    EngineeringLite,
    NonEngineering,
};

enum class TaskStatus {
    Complete,
    Partial,
    Failed,
    Degraded,
};

enum class VerificationGate {
    Contract,
    Unit,
    Dimensional,
    Provenance,
    Contradiction,
    Assumption,
    AdversarialFalsification,
    ConfidenceCalibration,
};

enum class GateResult {
    Pass,
    Fail,
    Warn,
};

enum class NoteType {
    Finding,
    Derivation,
    Decision,
    Gap,
    Synthesis,
    AgentThinking,
    IlcLink,
};

enum class OutputType {
    Analysis,
    Critique,
    Verification,
    MemoryOp,
    Synthesis,
};

enum class ProviderStatus {
    Healthy,
    Degraded,
    Unavailable,
};

std::string_view to_string(TaskType);
std::string_view to_string(TaskStatus);
std::string_view to_string(VerificationGate);
std::string_view to_string(GateResult);
std::string_view to_string(NoteType);
std::string_view to_string(ProviderStatus);

} // namespace forge::common

/**
 * @file enums.cpp
 * @brief to_string() implementations for all FORGE enums.
 */

#include "forge/common/enums.hpp"

namespace forge::common {

std::string_view to_string(TaskType v) {
    switch (v) {
        case TaskType::EngineeringFull:  return "engineering_full";
        case TaskType::EngineeringLite:  return "engineering_lite";
        case TaskType::NonEngineering:   return "non_engineering";
    }
    return "unknown";
}

std::string_view to_string(TaskStatus v) {
    switch (v) {
        case TaskStatus::Complete:   return "complete";
        case TaskStatus::Partial:    return "partial";
        case TaskStatus::Failed:     return "failed";
        case TaskStatus::Degraded:   return "degraded";
    }
    return "unknown";
}

std::string_view to_string(VerificationGate v) {
    switch (v) {
        case VerificationGate::Contract:                  return "contract";
        case VerificationGate::Unit:                      return "unit";
        case VerificationGate::Dimensional:               return "dimensional";
        case VerificationGate::Provenance:                return "provenance";
        case VerificationGate::Contradiction:             return "contradiction";
        case VerificationGate::Assumption:                return "assumption";
        case VerificationGate::AdversarialFalsification:  return "adversarial_falsification";
        case VerificationGate::ConfidenceCalibration:     return "confidence_calibration";
    }
    return "unknown";
}

std::string_view to_string(GateResult v) {
    switch (v) {
        case GateResult::Pass: return "pass";
        case GateResult::Fail: return "fail";
        case GateResult::Warn: return "warn";
    }
    return "unknown";
}

std::string_view to_string(NoteType v) {
    switch (v) {
        case NoteType::Finding:       return "finding";
        case NoteType::Derivation:    return "derivation";
        case NoteType::Decision:      return "decision";
        case NoteType::Gap:           return "gap";
        case NoteType::Synthesis:     return "synthesis";
        case NoteType::AgentThinking: return "agent-thinking";
        case NoteType::IlcLink:       return "ilc-link";
    }
    return "unknown";
}

std::string_view to_string(ProviderStatus v) {
    switch (v) {
        case ProviderStatus::Healthy:     return "healthy";
        case ProviderStatus::Degraded:    return "degraded";
        case ProviderStatus::Unavailable: return "unavailable";
    }
    return "unknown";
}

} // namespace forge::common

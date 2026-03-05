#pragma once
#include <string_view>

/// Error code constants matching docs/contracts/error-codes.md v1.
namespace forge::logging::codes {

// Contract
constexpr std::string_view ERR_CONTRACT_VIOLATION         = "ERR_CONTRACT_VIOLATION";
constexpr std::string_view ERR_CONTRACT_VERSION_MISSING   = "ERR_CONTRACT_VERSION_MISSING";
constexpr std::string_view ERR_CONTRACT_VERSION_INCOMPAT  = "ERR_CONTRACT_VERSION_INCOMPATIBLE";

// Unit / Dimensional
constexpr std::string_view ERR_UNIT_MISSING               = "ERR_UNIT_MISSING";
constexpr std::string_view ERR_UNIT_INCONSISTENT          = "ERR_UNIT_INCONSISTENT";
constexpr std::string_view ERR_UNIT_NORMALIZATION_FAIL    = "ERR_UNIT_NORMALIZATION_FAIL";
constexpr std::string_view ERR_DIMENSIONAL_MISMATCH       = "ERR_DIMENSIONAL_MISMATCH";
constexpr std::string_view ERR_DIMENSIONAL_INCOMPATIBLE   = "ERR_DIMENSIONAL_INCOMPATIBLE";

// Provenance
constexpr std::string_view ERR_PROVENANCE_MISSING         = "ERR_PROVENANCE_MISSING";
constexpr std::string_view ERR_PROVENANCE_UNSPECIFIC      = "ERR_PROVENANCE_UNSPECIFIC";
constexpr std::string_view ERR_PROVENANCE_UNPARSEABLE     = "ERR_PROVENANCE_UNPARSEABLE";
constexpr std::string_view WARN_PROVENANCE_UNVERIFIED     = "WARN_PROVENANCE_UNVERIFIED";

// Tool
constexpr std::string_view ERR_TOOL_SUBPROCESS_FAIL       = "ERR_TOOL_SUBPROCESS_FAIL";
constexpr std::string_view ERR_TOOL_TIMEOUT               = "ERR_TOOL_TIMEOUT";
constexpr std::string_view ERR_TOOL_OUTPUT_INVALID        = "ERR_TOOL_OUTPUT_INVALID";
constexpr std::string_view ERR_TOOL_SANDBOX_VIOLATION     = "ERR_TOOL_SANDBOX_VIOLATION";
constexpr std::string_view WARN_TOOL_DEGRADED             = "WARN_TOOL_DEGRADED";

// Vault
constexpr std::string_view ERR_VAULT_WRITE_FAIL           = "ERR_VAULT_WRITE_FAIL";
constexpr std::string_view ERR_VAULT_READ_FAIL            = "ERR_VAULT_READ_FAIL";
constexpr std::string_view ERR_VAULT_AMNESIA              = "ERR_VAULT_AMNESIA";
constexpr std::string_view ERR_VAULT_SCHEMA_INVALID       = "ERR_VAULT_SCHEMA_INVALID";
constexpr std::string_view ERR_VAULT_CONTRADICTION        = "ERR_VAULT_CONTRADICTION";

// Provider
constexpr std::string_view ERR_PROVIDER_UNAVAILABLE       = "ERR_PROVIDER_UNAVAILABLE";
constexpr std::string_view ERR_PROVIDER_RATE_LIMITED      = "ERR_PROVIDER_RATE_LIMITED";
constexpr std::string_view ERR_PROVIDER_TIMEOUT           = "ERR_PROVIDER_TIMEOUT";
constexpr std::string_view ERR_PROVIDER_INVALID_RESPONSE  = "ERR_PROVIDER_INVALID_RESPONSE";

// Verification
constexpr std::string_view ERR_VERIFY_GATE_FAIL           = "ERR_VERIFY_GATE_FAIL";
constexpr std::string_view ERR_VERIFY_HIDDEN_ASSUMPTION   = "ERR_VERIFY_HIDDEN_ASSUMPTION";
constexpr std::string_view ERR_CONTRADICTION_DETECTED     = "ERR_CONTRADICTION_DETECTED";
constexpr std::string_view WARN_CONFIDENCE_MISMATCH       = "WARN_CONFIDENCE_MISMATCH";
constexpr std::string_view WARN_ADVERSARIAL_CHALLENGE     = "WARN_ADVERSARIAL_CHALLENGE";

// System
constexpr std::string_view ERR_SYSTEM_UNKNOWN             = "ERR_SYSTEM_UNKNOWN";
constexpr std::string_view ERR_SYSTEM_LOOP_GUARD          = "ERR_SYSTEM_LOOP_GUARD";
constexpr std::string_view ERR_SYSTEM_CONFIG_INVALID      = "ERR_SYSTEM_CONFIG_INVALID";

} // namespace forge::logging::codes

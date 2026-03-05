#pragma once
#include "forge/common/result.hpp"
#include <string>
#include <memory>

namespace forge::config {

/// Top-level FORGE configuration loaded from forge.yaml.
struct ForgeConfig {
    struct RouterConfig {
        std::vector<std::string> provider_chain;
        int health_check_interval_s{30};
        int max_retries_per_provider{2};
        bool allow_degraded_mode{true};
    };
    struct OrchestratorConfig {
        int max_loop_iterations{5};
        int max_tool_retries{3};
    };
    struct VaultConfig {
        std::string vault_path;    ///< Path to forge-vault/ directory
        bool git_auto_commit{true};
    };

    RouterConfig       router;
    OrchestratorConfig orchestrator;
    VaultConfig        vault;
    std::string        log_output;  ///< "stdout" | file path
    std::string        schema_version;
};

/// Loads and validates FORGE configuration from YAML files.
class ConfigLoader {
public:
    /// Load config from a YAML file path.
    static forge::common::Result<ForgeConfig> load(const std::string& path);

    /// Load from a YAML string (for testing).
    static forge::common::Result<ForgeConfig> load_string(const std::string& yaml);

    /// Validate a loaded config against the schema.
    static forge::common::VoidResult validate(const ForgeConfig& config);
};

} // namespace forge::config

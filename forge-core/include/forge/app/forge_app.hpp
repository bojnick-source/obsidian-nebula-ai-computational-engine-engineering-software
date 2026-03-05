#pragma once
#include "forge/config/config_loader.hpp"
#include "forge/orchestration/orchestrator.hpp"
#include "forge/logging/jsonl_logger.hpp"
#include <memory>

namespace forge::app {

/// Top-level FORGE application. Owns all subsystem instances.
class ForgeApp {
public:
    struct AppConfig {
        std::string config_path{"forge-core/configs/forge.yaml"};
    };

    static forge::common::Result<std::unique_ptr<ForgeApp>> create(
        const AppConfig& app_config);

    /// Execute a task.
    forge::common::Result<forge::orchestration::TaskResult> execute(
        const forge::orchestration::TaskRequest& request);

    /// Run startup diagnostics (smoke tests for vault, providers, tools).
    forge::common::VoidResult startup_check();

    /// Graceful shutdown.
    void shutdown();

private:
    ForgeApp() = default;

    forge::config::ForgeConfig config_;
    std::unique_ptr<forge::orchestration::Orchestrator> orchestrator_;
    std::shared_ptr<forge::logging::JsonlLogger> logger_;
};

} // namespace forge::app

#pragma once
#include "forge/orchestration/task_graph.hpp"
#include "forge/orchestration/specialist_dispatch.hpp"
#include "forge/orchestration/escalation.hpp"
#include "forge/blackboard/blackboard.hpp"
#include "forge/common/result.hpp"
#include "forge/common/enums.hpp"
#include <memory>
#include <string>

namespace forge::orchestration {

struct TaskRequest {
    std::string                  description;
    forge::common::TaskType      task_type;
    std::string                  project;      ///< e.g., "aladdin-3b"
    std::string                  component;    ///< e.g., "motor_mount_bracket"
};

struct TaskResult {
    std::string                  trace_id;
    forge::common::TaskStatus    status;
    std::string                  result_summary;
    std::vector<std::string>     unresolved_gaps;
    std::vector<std::string>     what_would_falsify;
    float                        confidence{0.0f};
    std::vector<std::string>     artifact_refs;
};

/// Top-level orchestrator. Drives the 9-phase core loop.
class Orchestrator {
public:
    struct Config {
        int max_loop_iterations{5};
        int max_tool_retries{3};
        bool allow_degraded_mode{true};
    };

    explicit Orchestrator(Config config,
                          std::unique_ptr<SpecialistDispatch> dispatch,
                          std::unique_ptr<EscalationHandler>  escalation);

    /// Execute a task end-to-end. Creates a new blackboard for the task.
    forge::common::Result<TaskResult> execute(const TaskRequest& request);

private:
    forge::common::VoidResult run_phase_intake(
        forge::blackboard::Blackboard& bb, const TaskRequest& req);

    forge::common::VoidResult run_phase_routing(
        forge::blackboard::Blackboard& bb);

    forge::common::VoidResult run_phase_decomposition(
        forge::blackboard::Blackboard& bb);

    forge::common::VoidResult run_phase_memory_preflight(
        forge::blackboard::Blackboard& bb);

    forge::common::VoidResult run_phase_specialist(
        forge::blackboard::Blackboard& bb);

    forge::common::VoidResult run_phase_tool_execution(
        forge::blackboard::Blackboard& bb);

    forge::common::VoidResult run_phase_verification(
        forge::blackboard::Blackboard& bb);

    forge::common::VoidResult run_phase_persistence(
        forge::blackboard::Blackboard& bb);

    TaskResult assemble_output(const forge::blackboard::Blackboard& bb);

    Config config_;
    std::unique_ptr<SpecialistDispatch> dispatch_;
    std::unique_ptr<EscalationHandler>  escalation_;
};

} // namespace forge::orchestration

#pragma once
#include "forge/blackboard/blackboard.hpp"
#include "forge/common/result.hpp"
#include <string>

namespace forge::orchestration {

/// Dispatches the appropriate specialist agent for a given task.
class SpecialistDispatch {
public:
    virtual ~SpecialistDispatch() = default;

    /// Select and invoke the appropriate specialist for the task in `bb`.
    /// Writes specialist output back to the blackboard.
    virtual forge::common::VoidResult dispatch(
        forge::blackboard::Blackboard& bb) = 0;

    /// Return the agent_id of the specialist that would be selected for this domain.
    virtual std::string select_agent(const std::string& domain) const = 0;
};

} // namespace forge::orchestration

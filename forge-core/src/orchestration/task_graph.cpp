/**
 * @file task_graph.cpp
 * @brief DAG of task phases for a single FORGE execution.
 *
 * Currently sequential for MVP.  DAG support enables future parallelism:
 * e.g., tool_execution and memory_preflight can run concurrently once
 * decomposition writes all required blackboard fields.
 */

#include "forge/orchestration/task_graph.hpp"

#include <algorithm>
#include <stdexcept>

namespace forge::orchestration {

void TaskGraph::add_node(TaskNode node) {
    std::string id = node.id;
    nodes_[id] = std::move(node);
    order_.push_back(id);
}

void TaskGraph::mark_complete(const std::string& node_id) {
    auto it = nodes_.find(node_id);
    if (it != nodes_.end()) {
        it->second.completed = true;
    }
}

void TaskGraph::mark_failed(const std::string& node_id) {
    auto it = nodes_.find(node_id);
    if (it != nodes_.end()) {
        it->second.failed = true;
    }
}

std::vector<std::string> TaskGraph::ready_nodes() const {
    std::vector<std::string> ready;
    for (const auto& id : order_) {
        const auto& node = nodes_.at(id);
        if (node.completed || node.failed) continue;

        bool deps_done = std::all_of(
            node.depends_on.begin(), node.depends_on.end(),
            [this](const std::string& dep_id) {
                auto it = nodes_.find(dep_id);
                return it != nodes_.end() && it->second.completed;
            }
        );
        if (deps_done) ready.push_back(id);
    }
    return ready;
}

bool TaskGraph::is_complete() const {
    return std::all_of(nodes_.begin(), nodes_.end(),
        [](const auto& kv) { return kv.second.completed; });
}

bool TaskGraph::has_failure() const {
    return std::any_of(nodes_.begin(), nodes_.end(),
        [](const auto& kv) { return kv.second.failed; });
}

} // namespace forge::orchestration

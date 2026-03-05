#pragma once
#include <string>
#include <vector>
#include <unordered_map>

namespace forge::orchestration {

/// A node in the task graph (a phase or sub-task).
struct TaskNode {
    std::string id;
    std::string phase_name;
    std::vector<std::string> depends_on; ///< IDs of prerequisite nodes
    bool completed{false};
    bool failed{false};
};

/// Directed acyclic graph of task phases for a single execution.
/// Currently sequential for MVP; DAG support enables future parallelism.
class TaskGraph {
public:
    void add_node(TaskNode node);
    void mark_complete(const std::string& node_id);
    void mark_failed(const std::string& node_id);

    /// Return nodes whose dependencies are all complete (ready to execute).
    std::vector<std::string> ready_nodes() const;

    /// Return true if all nodes are complete.
    bool is_complete() const;

    /// Return true if any node has failed.
    bool has_failure() const;

private:
    std::unordered_map<std::string, TaskNode> nodes_;
    std::vector<std::string> order_; ///< Insertion order
};

} // namespace forge::orchestration

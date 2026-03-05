#pragma once
#include <string>
#include <vector>
#include <unordered_map>
#include <optional>

namespace forge::a2a {

/// Agent card loaded from YAML (forge-agents/registry/agent_cards/).
struct AgentCard {
    std::string              id;
    std::string              name;
    std::string              version;
    std::string              role;             ///< specialist | antagonist | verifier | librarian
    std::string              domain;
    std::vector<std::string> capabilities;
    std::vector<std::string> tools_allowed;
    std::string              output_contract_ref;
    std::string              prompt_ref;
    std::string              antagonist_pair;  ///< if role == specialist
};

/// Registry of all agent cards.
class AgentCardRegistry {
public:
    void register_card(AgentCard card);

    std::optional<AgentCard> find(const std::string& agent_id) const;

    /// Find all specialists for a given domain.
    std::vector<AgentCard> specialists_for_domain(const std::string& domain) const;

    /// Find all agents with a given role.
    std::vector<AgentCard> agents_with_role(const std::string& role) const;

private:
    std::unordered_map<std::string, AgentCard> cards_;
};

} // namespace forge::a2a

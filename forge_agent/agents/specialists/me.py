# RELOCATED — forge_agent/agents/specialists/me.py
#
# Mechanical Engineer agent moved to:
#   forge_agent/agents/engineers/mechanical_engineer.py
#
# "me.py" was an ambiguous abbreviation. The new filename matches ROLE value.
# ME belongs in engineers/, not specialists/.

from forge_agent.agents.engineers.mechanical_engineer import (  # noqa: F401
    MODEL,
    ROLE,
    SYSTEM_PROMPT,
    TEMPERATURE,
)

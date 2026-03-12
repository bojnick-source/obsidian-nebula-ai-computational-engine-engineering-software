# RELOCATED — forge_agent/agents/specialists/ee.py
#
# Electrical Engineer agent moved to:
#   forge_agent/agents/engineers/electrical_engineer.py
#
# "ee.py" was an ambiguous abbreviation. The new filename matches ROLE value.
# EE belongs in engineers/, not specialists/.

from forge_agent.agents.engineers.electrical_engineer import (  # noqa: F401
    MODEL,
    ROLE,
    SYSTEM_PROMPT,
    TEMPERATURE,
)

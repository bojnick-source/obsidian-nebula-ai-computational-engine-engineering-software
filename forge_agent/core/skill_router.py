"""
SkillRouter — cheap model selects relevant skills, specialist agents, and MCP servers
for a given engineering problem statement.

Uses claude-haiku (routing tier, T=0.0) for low-cost routing.
Falls back to keyword heuristics if the LLM call fails.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RoutingDecision:
    skills: list[str]
    agents: list[str]
    mcp_servers: list[str]
    rationale: str


# Keyword → skill heuristics (fallback)
_KEYWORD_SKILL_MAP: dict[str, list[str]] = {
    r"\bfea\b|finite.element|stress|strain|fatigue|buckling": ["fea"],
    r"\bcfd\b|fluid|flow|thermal|heat|convection|turbulence": ["cfd"],
    r"\btopolog|topo.opt|simp|density.filter": ["topology_optimization"],
    r"\bcad\b|geometry|mesh|solid|shell|surface|stl": ["cad_mesh"],
    r"\bmatlab\b|simulink|control|pid|transfer.function|bode|nyquist": ["controls"],
    r"\bpcb\b|schematic|electrical|circuit|wiring|harness|emi": ["ee"],
    r"\bnoise\b|acoustic|vibration|nv[h]?\b|frequency.response": ["acoustics"],
    r"\bmaterial|alloy|composite|fatigue.life|s.n.curve|crack": ["materials"],
    r"\bplasma|arc|discharge|mhd|magnetohydrodynamic": ["plasma"],
    r"\bbio\b|medical|implant|tissue|biomedical|fda": ["biomedical"],
    r"\boptimiz|gradient.descent|lagrange|convex|lp\b|nlp\b": ["optimization"],
    r"\bpde\b|partial.diff|laplace|poisson|wave.equation|heat.equation": ["pde"],
    r"\bnumerical|runge.kutta|euler.method|newton.method|finite.diff": ["numerical"],
    r"\btopolog|manifold|knot|homolog|homotopy": ["geometry_topology"],
    r"\bprobabilit|stochastic|monte.carlo|bayesian|uncertainty|reliability": ["probability_stats"],
    r"\bassembl|fastener|torque.spec|dfa|disassembl|maintenance": ["assembly"],
}

_SKILL_AGENT_MAP: dict[str, list[str]] = {
    "fea": ["mechanical_engineer", "mathematician_numerical"],
    "cfd": ["thermal_fluids_engineer", "mathematician_pde"],
    "topology_optimization": ["mechanical_engineer", "mathematician_optimization"],
    "cad_mesh": ["mechanical_engineer"],
    "controls": ["controls_engineer", "systems_engineer"],
    "ee": ["electrical_engineer", "systems_engineer"],
    "acoustics": ["acoustics_engineer"],
    "materials": ["materials_engineer"],
    "plasma": ["plasma_engineer"],
    "biomedical": ["biomedical_engineer"],
    "optimization": ["mathematician_optimization"],
    "pde": ["mathematician_pde"],
    "numerical": ["mathematician_numerical"],
    "geometry_topology": ["mathematician_geometry_topology"],
    "probability_stats": ["mathematician_probability_stats"],
    "assembly": ["mechanical_engineer"],
}


class SkillRouter:
    """Routes a problem statement to skills, agents, and MCP servers."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        cfg_dir = Path(__file__).parent.parent / "config"
        self._skill_server_map: dict[str, list[str]] = self._load_yaml(
            config_path or cfg_dir / "skill_server_map.yaml"
        ).get("skill_server_map", {})

    async def route(
        self,
        problem: str,
        llm_client: Any | None = None,
        model: str = "claude-haiku-4-5-20251001",
    ) -> RoutingDecision:
        """
        Primary: ask cheap LLM to select skills.
        Fallback: keyword heuristics.
        """
        if llm_client is not None:
            try:
                return await self._llm_route(problem, llm_client, model)
            except Exception:
                pass
        return self._keyword_route(problem)

    # ---------------------------------------------------------------- private

    async def _llm_route(
        self, problem: str, client: Any, model: str
    ) -> RoutingDecision:
        all_skills = list(_SKILL_AGENT_MAP.keys())
        prompt = (
            "You are a routing model. Given the engineering problem below, "
            "select the most relevant skills from this list:\n"
            f"{all_skills}\n\n"
            "Respond with a JSON object: "
            '{"skills": [...], "rationale": "..."}\n\n'
            f"Problem:\n{problem}"
        )
        msg = await client.messages.create(
            model=model,
            max_tokens=256,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = msg.content[0].text.strip()
        # Extract JSON from possible markdown fence
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            data = json.loads(m.group())
        else:
            data = json.loads(text)

        skills: list[str] = [s for s in data.get("skills", []) if s in _SKILL_AGENT_MAP]
        if not skills:
            skills = ["fea"]  # safe default
        return self._build_decision(skills, data.get("rationale", "LLM routed"))

    def _keyword_route(self, problem: str) -> RoutingDecision:
        text = problem.lower()
        matched: list[str] = []
        for pattern, skills in _KEYWORD_SKILL_MAP.items():
            if re.search(pattern, text):
                for s in skills:
                    if s not in matched:
                        matched.append(s)
        if not matched:
            matched = ["fea"]
        return self._build_decision(matched, "keyword heuristic")

    def _build_decision(self, skills: list[str], rationale: str) -> RoutingDecision:
        agents: list[str] = []
        for s in skills:
            for a in _SKILL_AGENT_MAP.get(s, []):
                if a not in agents:
                    agents.append(a)

        servers: list[str] = []
        for s in skills:
            for srv in self._skill_server_map.get(s, []):
                if srv not in servers:
                    servers.append(srv)

        return RoutingDecision(
            skills=skills,
            agents=agents,
            mcp_servers=servers,
            rationale=rationale,
        )

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        if not path.exists():
            return {}
        with path.open() as f:
            return yaml.safe_load(f) or {}

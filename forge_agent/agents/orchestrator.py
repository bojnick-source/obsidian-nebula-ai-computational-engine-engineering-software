# DEPRECATED — forge_agent/agents/orchestrator.py (v1)
#
# Superseded by forge_agent/core/multi_agent_orchestrator.py (v2).
# v2 fixes: XML output parsing (not json.loads), real dependency graph
# (topological sort + asyncio.gather), vault write persistence.
#
# unified_agent.py now imports from core.multi_agent_orchestrator.
# This file is kept for reference only. Do not import in new code.

"""
MultiAgentOrchestrator — committee mode (v1 — DEPRECATED).

Lifecycle per problem:
  1. Route → select specialists + mathematicians
  2. Each specialist solves independently (parallel)
  3. Verifier reviews each output
  4. If disputes → specialists revise (max committee_max_revisions rounds)
  5. Verifier synthesises final_answer onto blackboard
  6. Librarian writes 5 vault notes
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


from forge_agent.core.verifier import VerificationResult, VerifierAgent
from forge_agent.core.logger import AgentLogger
from forge_agent.core.mcp_manager import MCPManager
from forge_agent.core.ptc_engine import PTCEngine
from forge_agent.core.retry import RetryConfig, retry_api_call
from forge_agent.core.skill_router import SkillRouter
from forge_agent.core.token_budget import TokenBudget
from forge_agent.memory.obsidian_manager import ObsidianVaultManager


# ------------------------------------------------------------------ result


@dataclass
class CommitteeResult:
    problem_id: str
    final_answer: str
    blackboard: dict
    specialist_outputs: dict[str, str] = field(default_factory=dict)
    verifications: dict[str, VerificationResult] = field(default_factory=dict)
    disputes: list[dict] = field(default_factory=list)
    vault_notes_written: list[str] = field(default_factory=list)
    rounds: int = 0


# ------------------------------------------------------------------ prompt builders


def _specialist_prompt(role: str, problem: str, blackboard: dict) -> str:
    return f"""\
You are the FORGE {role.replace("_", " ").title()} specialist.

Solve the engineering problem below. You MUST return a JSON object satisfying
the Agent Output Contract:
{{
  "model_choice": "...",
  "equations": ["LaTeX eq 1", ...],
  "units": "SI throughout",
  "sanity_checks": [{{ "type": "limiting_case|conservation|dimensional", "detail": "..." }}],
  "calculation_path": "step-by-step ...",
  "numerical_answer": "...",
  "assumptions": ["..."]
}}

Current blackboard:
```json
{json.dumps(blackboard, indent=2, default=str)[:2000]}
```

Problem:
{problem}
"""


def _synthesis_prompt(blackboard: dict, specialist_outputs: dict) -> str:
    outputs_text = "\n\n".join(
        f"### {role}\n{output[:1500]}"
        for role, output in specialist_outputs.items()
    )
    return f"""\
You are the FORGE Synthesis Verifier.

All specialists have solved the problem. Synthesise their outputs into
a single, verified final answer. Resolve any disagreements and produce:
{{
  "final_answer": "...",
  "key_equations": ["..."],
  "confidence": 0.0-1.0,
  "resolution_notes": "..."
}}

Specialist outputs:
{outputs_text}

Blackboard:
```json
{json.dumps(blackboard, indent=2, default=str)[:1500]}
```
"""


# ------------------------------------------------------------------ orchestrator


class MultiAgentOrchestrator:
    def __init__(
        self,
        config: dict,
        router_cfg: dict,
        run_id: str | None = None,
        log_dir: str | Path = "/tmp/forge_agent_logs",
    ) -> None:
        self.config = config
        self.router_cfg = router_cfg
        self.run_id = run_id or str(uuid.uuid4())[:8]

        agent_cfg = config.get("agent", {})
        self.max_revisions: int = agent_cfg.get("committee_max_revisions", 3)
        self.token_budget = TokenBudget(
            total_budget=agent_cfg.get("token_budget", 180_000),
        )
        self.skill_router = SkillRouter()
        self.mcp = MCPManager()
        self.ptc = PTCEngine()
        self.logger = AgentLogger(
            log_path=Path(log_dir) / f"{self.run_id}_committee.jsonl",
            run_id=self.run_id,
        )

        vault_path = config.get("vault_path", "/tmp/forge_vault")
        self._vault: ObsidianVaultManager | None = None
        self._vault_path = vault_path
        self._client: Any = None
        self._verifier: VerifierAgent | None = None

    async def setup(self) -> None:
        import anthropic
        self._client = anthropic.AsyncAnthropic()
        self._verifier = VerifierAgent(self._client)
        self._vault = ObsidianVaultManager(self._vault_path, llm_client=self._client)
        await self._vault.start()
        await self.mcp.start()

    async def teardown(self) -> None:
        await self.mcp.stop()
        if self._vault:
            await self._vault.flush()
        self.logger.close()

    async def solve(self, problem: str) -> CommitteeResult:
        problem_id = f"PROB-{self.run_id}"
        blackboard: dict = {
            "problem_id": problem_id,
            "problem_statement": problem,
            "assumptions": [],
            "governing_equations": [],
            "unknowns": [],
            "constraints": [],
            "derivation_steps": [],
            "checks": {},
            "numerical_examples": [],
            "disagreements": [],
        }

        routing = await self.skill_router.route(problem, self._client)
        self.logger.log_phase("routing", "completed", {"agents": routing.agents})

        specialist_outputs: dict[str, str] = {}
        verifications: dict[str, VerificationResult] = {}

        # Revision loop
        for revision in range(self.max_revisions):
            self.logger.log_phase("committee_round", "started", {"round": revision + 1})

            # Parallel specialist calls
            tasks = {
                role: asyncio.create_task(
                    self._call_specialist(role, problem, blackboard),
                    name=f"specialist-{role}",
                )
                for role in routing.agents
                if "mathematician" not in role  # mathematicians go second
            }
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for role, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    specialist_outputs[role] = f"ERROR: {result}"
                else:
                    specialist_outputs[role] = result

            # Verify each output
            all_validated = True
            for role, output in specialist_outputs.items():
                vr = await self._verifier.verify(output, blackboard, role)
                verifications[role] = vr
                if vr.overall_verdict != "validated":
                    all_validated = False

            if all_validated:
                self.logger.log_phase("committee_round", "completed", {"round": revision + 1, "all_validated": True})
                break
            self.logger.log_phase("committee_round", "completed", {"round": revision + 1, "all_validated": False})

        # Mathematician pass (sequential — build on specialist work)
        math_agents = [a for a in routing.agents if "mathematician" in a]
        for math_role in math_agents:
            output = await self._call_specialist(math_role, problem, blackboard)
            specialist_outputs[math_role] = output
            vr = await self._verifier.verify(output, blackboard, math_role)
            verifications[math_role] = vr

        # Synthesis
        final_answer = await self._synthesise(blackboard, specialist_outputs)
        blackboard["final_answer"] = final_answer

        # Write vault notes
        vault_notes = await self._write_vault_notes(problem_id, problem, blackboard, specialist_outputs)

        return CommitteeResult(
            problem_id=problem_id,
            final_answer=final_answer,
            blackboard=blackboard,
            specialist_outputs=specialist_outputs,
            verifications=verifications,
            disputes=blackboard.get("disagreements", []),
            vault_notes_written=vault_notes,
            rounds=self.max_revisions,
        )

    # ---------------------------------------------------------------- private

    async def _call_specialist(
        self, role: str, problem: str, blackboard: dict
    ) -> str:
        model = self._resolve_model(role)
        provider = self._resolve_provider(role)
        prompt = _specialist_prompt(role, problem, blackboard)

        if provider == "openai":
            import openai as _oai
            import os
            oai = _oai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = await retry_api_call(
                oai.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": "You are a FORGE engineering specialist. Follow the Agent Output Contract exactly."},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=4096,
                config=RetryConfig(),
            )
            return response.choices[0].message.content or ""

        # Default: Anthropic
        msg = await retry_api_call(
            self._client.messages.create,
            model=model,
            max_tokens=4096,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
            config=RetryConfig(),
        )
        return msg.content[0].text

    def _resolve_provider(self, role: str) -> str:
        """Returns the preferred provider for a role."""
        roles_cfg = self.router_cfg.get("roles", {})
        canonical = role.replace("-", "_")
        for key in roles_cfg:
            if key in canonical or canonical in key:
                return roles_cfg[key].get("preferred_provider", "anthropic")
        return "anthropic"

    async def _synthesise(
        self, blackboard: dict, specialist_outputs: dict[str, str]
    ) -> str:
        prompt = _synthesis_prompt(blackboard, specialist_outputs)
        msg = await retry_api_call(
            self._client.messages.create,
            model="claude-opus-4-6",
            max_tokens=2048,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
            config=RetryConfig(),
        )
        text = msg.content[0].text
        parsed = _try_parse_json(text)
        if parsed:
            return parsed.get("final_answer", text)
        return text

    async def _write_vault_notes(
        self,
        problem_id: str,
        problem: str,
        blackboard: dict,
        specialist_outputs: dict[str, str],
    ) -> list[str]:
        if not self._vault:
            return []
        notes_written = []
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        # 1. Problem definition
        await self._vault.write_note(
            title=f"{problem_id} - Problem Definition",
            content=f"# Problem\n{problem}\n\n## Blackboard\n```json\n{json.dumps(blackboard, indent=2, default=str)[:3000]}\n```",
            frontmatter={"problem_id": problem_id, "date": now, "type": "problem_definition"},
        )
        notes_written.append(f"{problem_id} - Problem Definition")

        # 2. Final answer
        await self._vault.write_note(
            title=f"{problem_id} - Final Answer",
            content=f"# Final Answer\n{blackboard.get('final_answer', 'N/A')}",
            frontmatter={"problem_id": problem_id, "date": now, "type": "answer"},
        )
        notes_written.append(f"{problem_id} - Final Answer")

        # 3. Specialist contributions
        for role, output in list(specialist_outputs.items())[:3]:
            title = f"{problem_id} - {role}"
            await self._vault.write_note(
                title=title,
                content=f"# {role}\n{output[:3000]}",
                frontmatter={"problem_id": problem_id, "date": now, "type": "specialist_output", "agent": role},
            )
            notes_written.append(title)

        return notes_written

    def _resolve_model(self, role: str) -> str:
        roles_cfg = self.router_cfg.get("roles", {})
        providers_cfg = self.router_cfg.get("providers", {})
        canonical = role.replace("-", "_")

        for key in roles_cfg:
            if key in canonical or canonical in key:
                rc = roles_cfg[key]
                provider = rc.get("preferred_provider", "anthropic")
                tier = rc.get("model_tier", "primary")
                model = providers_cfg.get(provider, {}).get("models", {}).get(tier)
                if model:
                    return model
                # Fallback provider
                fb_provider = rc.get("fallback_provider", "anthropic")
                fb_tier = rc.get("fallback_tier", "secondary")
                model = providers_cfg.get(fb_provider, {}).get("models", {}).get(fb_tier)
                if model:
                    return model

        return "claude-sonnet-4-6"


def _try_parse_json(text: str) -> dict | None:
    import re
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None

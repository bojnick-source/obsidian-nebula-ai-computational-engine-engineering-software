"""
UnifiedAgent — main FORGE agent loop.

Modes:
  single      — one specialist answers directly
  committee   — MultiAgentOrchestrator (verifier loop)
  interactive — interactive REPL (reads problem from stdin each iteration)

Entry point:
  forge --problem "..." [--mode single|committee|interactive] [--config path/to/forge.yaml]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import yaml

from forge_agent.core.container_state import ContainerState
from forge_agent.core.context_assembler import ObsidianAwareContextAssembler
from forge_agent.core.logger import AgentLogger
from forge_agent.core.loop_guard import AgentLoopGuard, LoopDivergenceError, LoopLimitError
from forge_agent.core.mcp_manager import MCPManager
from forge_agent.core.ptc_engine import PTCEngine
from forge_agent.core.retry import RetryConfig, retry_api_call
from forge_agent.core.shutdown import GracefulShutdown
from forge_agent.core.skill_router import SkillRouter
from forge_agent.core.token_budget import BudgetExhausted, TokenBudget


# ------------------------------------------------------------------ config


def _load_config(config_path: str | Path | None = None) -> dict:
    path = Path(config_path) if config_path else (
        Path(__file__).parent.parent / "config" / "forge.yaml"
    )
    if not path.exists():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}


def _load_model_router(config_path: str | Path | None = None) -> dict:
    path = Path(config_path) if config_path else (
        Path(__file__).parent.parent / "config" / "model_router.yaml"
    )
    if not path.exists():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}


# ------------------------------------------------------------------ providers


def _build_anthropic_client(api_key: str | None = None):
    import anthropic
    return anthropic.AsyncAnthropic(api_key=api_key)


def _resolve_model(router_cfg: dict, role: str, tier: str) -> tuple[str, str]:
    """Returns (model_id, provider) for a given role."""
    role_cfg = router_cfg.get("roles", {}).get(role, {})
    preferred_tier = role_cfg.get("model_tier", tier)
    preferred_provider = role_cfg.get("preferred_provider", "anthropic")

    providers_cfg = router_cfg.get("providers", {})
    provider_cfg = providers_cfg.get(preferred_provider, {})
    model = provider_cfg.get(preferred_tier, "claude-sonnet-4-6")
    return model, preferred_provider


# ------------------------------------------------------------------ core loop


class UnifiedAgent:
    """
    Single-agent runtime loop:
      tick() → get model response → handle tool_use / end_turn
    """

    TOOL_USE = "tool_use"
    END_TURN = "end_turn"
    MAX_TOOL_TURNS = 25

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
        self.token_budget = TokenBudget(
            total_budget=agent_cfg.get("token_budget", 180_000),
            max_vault_tokens=agent_cfg.get("max_vault_tokens", 4_000),
        )
        self.loop_guard = AgentLoopGuard(
            max_iterations=agent_cfg.get("max_iterations", 25)
        )
        self.ptc = PTCEngine(timeout_s=30.0)
        self.skill_router = SkillRouter()
        self.context_assembler = ObsidianAwareContextAssembler(
            base_prompt=config.get("base_prompt", _DEFAULT_SYSTEM_PROMPT),
            max_vault_tokens=agent_cfg.get("max_vault_tokens", 4_000),
            vault_top_k=agent_cfg.get("vault_top_k", 5),
        )
        self.mcp = MCPManager()
        self.logger = AgentLogger(
            log_path=Path(log_dir) / f"{self.run_id}.jsonl",
            run_id=self.run_id,
        )
        self.container = ContainerState()
        self.shutdown = GracefulShutdown(drain_timeout_s=10.0)

        self._client = None
        self._messages: list[dict] = []
        self._blackboard: dict = {}

    async def setup(self) -> None:
        providers = self.config.get("providers", {})
        anthropic_cfg = providers.get("anthropic", {})
        self._client = _build_anthropic_client(api_key=anthropic_cfg.get("api_key"))
        await self.mcp.start()
        self.shutdown.install_signal_handlers()
        await self.container.mark_ready()
        await self.container.mark_running()

    async def teardown(self) -> None:
        await self.mcp.stop()
        self.logger.close()
        if not self.container.is_terminal():
            await self.shutdown.drain_and_stop(self.container)

    async def solve(self, problem: str, role: str = "orchestrator") -> str:
        """Run the agent loop for a problem; return final answer text."""
        self.loop_guard.reset()
        self._messages = [{"role": "user", "content": problem}]

        routing = await self.skill_router.route(problem, self._client)
        self.logger.log_phase("routing", "completed", {"skills": routing.skills, "agents": routing.agents})

        model, provider = _resolve_model(self.router_cfg, role, "primary")

        # Build tool list: MCP tools + code_execution
        mcp_tools = await self.mcp.list_all_tools()
        tools = [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in mcp_tools
        ]
        tools.append(self.ptc.tool_spec())

        skill_prompts: dict[str, str] = {}
        answer = ""

        while not self.shutdown.requested:
            iteration = self.loop_guard.tick()

            ctx = await self.context_assembler.assemble(
                problem=problem,
                messages=self._messages,
                skills=routing.skills,
                skill_prompts=skill_prompts,
                blackboard=self._blackboard,
            )

            # Token budget enforcement
            try:
                msgs, system, tools_out, sp = self.token_budget.enforce(
                    ctx.messages, ctx.system_prompt, tools, list(skill_prompts.values())
                )
            except BudgetExhausted:
                self.logger.log_budget(iteration, 0, self.token_budget.total_budget, "exhausted")
                break

            # Model call
            t0 = time.perf_counter()
            try:
                response = await retry_api_call(
                    self._client.messages.create,
                    model=model,
                    max_tokens=8192,
                    system=system,
                    messages=msgs,
                    tools=tools_out or [],
                    config=RetryConfig(),
                )
            except RuntimeError as exc:
                self.logger.log_model_call(
                    agent_role=role, model=model, provider=provider,
                    input_tokens=0, output_tokens=0,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    error=str(exc), iteration=iteration,
                )
                break

            latency_ms = (time.perf_counter() - t0) * 1000
            usage = getattr(response, "usage", None)
            in_tok = getattr(usage, "input_tokens", 0)
            out_tok = getattr(usage, "output_tokens", 0)
            self.logger.log_model_call(
                agent_role=role, model=model, provider=provider,
                input_tokens=in_tok, output_tokens=out_tok,
                latency_ms=latency_ms,
                stop_reason=response.stop_reason,
                iteration=iteration,
            )

            # Append assistant message
            self._messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == self.END_TURN:
                # Extract text
                for block in response.content:
                    if hasattr(block, "text"):
                        answer = block.text
                break

            if response.stop_reason == self.TOOL_USE:
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    tool_name = block.name
                    tool_args = block.input

                    try:
                        self.loop_guard.record_tool_call(tool_name, tool_args)
                    except LoopDivergenceError as exc:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"ERROR: {exc}",
                        })
                        continue

                    t_tool = time.perf_counter()
                    result = None
                    error = None
                    try:
                        if tool_name == "code_execution":
                            exec_result = await self.ptc.execute(tool_args.get("code", ""))
                            result = exec_result.to_tool_result()
                        else:
                            result = await self.mcp.call_tool(tool_name, tool_args)
                    except Exception as exc:
                        error = str(exc)
                        result = f"ERROR: {exc}"

                    tool_latency = (time.perf_counter() - t_tool) * 1000
                    self.logger.log_tool_call(
                        tool_name=tool_name,
                        tool_args=tool_args,
                        result=result,
                        latency_ms=tool_latency,
                        iteration=iteration,
                        error=error,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)[:8000],
                    })

                self._messages.append({"role": "user", "content": tool_results})

        return answer or "[No answer generated]"


# ------------------------------------------------------------------ CLI


_DEFAULT_SYSTEM_PROMPT = """\
You are FORGE — a production engineering AI assistant built for Reid Industries / Quantanium.
You apply rigorous physics, verified mathematics, and engineering standards to every problem.
Always show your work: state assumptions, governing equations, units (SI), and sanity checks.
"""


async def _run_single(args: argparse.Namespace) -> None:
    cfg = _load_config(args.config)
    router_cfg = _load_model_router()
    agent = UnifiedAgent(cfg, router_cfg)
    await agent.setup()
    try:
        answer = await agent.solve(args.problem)
        print("\n" + "=" * 60)
        print(answer)
        print("=" * 60)
        print(f"\nRun summary: {agent.logger.summary()}")
    finally:
        await agent.teardown()


async def _run_committee(args: argparse.Namespace) -> None:
    from forge_agent.agents.orchestrator import MultiAgentOrchestrator
    cfg = _load_config(args.config)
    router_cfg = _load_model_router()
    orch = MultiAgentOrchestrator(cfg, router_cfg)
    await orch.setup()
    try:
        result = await orch.solve(args.problem)
        print("\n" + "=" * 60)
        print(result.final_answer)
        print("=" * 60)
        if result.disputes:
            print(f"\nDisputes: {result.disputes}")
    finally:
        await orch.teardown()


async def _run_interactive(args: argparse.Namespace) -> None:
    cfg = _load_config(args.config)
    router_cfg = _load_model_router()
    agent = UnifiedAgent(cfg, router_cfg)
    await agent.setup()
    print("FORGE interactive mode. Type 'exit' to quit.\n")
    try:
        while True:
            try:
                problem = input("forge> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if problem.lower() in ("exit", "quit", "q"):
                break
            if not problem:
                continue
            answer = await agent.solve(problem)
            print(f"\n{answer}\n")
    finally:
        await agent.teardown()


def cli_main() -> None:
    parser = argparse.ArgumentParser(
        prog="forge",
        description="FORGE Unified Engineering Agent",
    )
    parser.add_argument("--problem", "-p", type=str, help="Engineering problem statement")
    parser.add_argument(
        "--mode", "-m",
        choices=["single", "committee", "interactive"],
        default="single",
    )
    parser.add_argument("--config", "-c", type=str, default=None, help="Path to forge.yaml")
    args = parser.parse_args()

    if args.mode == "interactive":
        asyncio.run(_run_interactive(args))
    elif args.mode == "committee":
        if not args.problem:
            parser.error("--problem is required for committee mode")
        asyncio.run(_run_committee(args))
    else:
        if not args.problem:
            parser.error("--problem is required for single mode")
        asyncio.run(_run_single(args))


if __name__ == "__main__":
    cli_main()

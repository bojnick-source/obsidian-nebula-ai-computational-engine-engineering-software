"""
MCPManager — connect, health-monitor, and call MCP servers.

Dispatch order (CLI-first):
  1. CliDispatcher — direct Python/subprocess call, no JSON-RPC overhead.
     Registered handlers: filesystem, vault, gmsh, calculix, freecad, MATLAB.
  2. MCP fallback — used when no CLI handler exists or CLI raises CliToolError.

Each MCP server gets its own CircuitBreaker. Calls are routed through
retry_api_call → circuit breaker → stdio JSON-RPC transport.

Server config: forge_agent/config/servers.yaml
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from forge_agent.core.retry import CircuitBreaker, retry_api_call
from forge_agent.core.cli_dispatcher import CliDispatcher


@dataclass
class ServerConfig:
    name: str
    command: list[str]
    timeout_ms: int = 5000
    health_check_interval_s: float = 30.0
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict


class MCPConnectionError(RuntimeError):
    pass


class MCPServer:
    """Manages a single MCP server subprocess (stdio transport)."""

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.name = config.name
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout_s=60.0)
        self._proc: asyncio.subprocess.Process | None = None
        self._tools: list[ToolSpec] = []
        self._msg_id: int = 0
        self._healthy: bool = False
        self._last_health_check: float = 0.0
        self._reader_task: asyncio.Task | None = None
        self._pending: dict[int, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            *self.config.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**__import__("os").environ, **self.config.env},
        )
        self._reader_task = asyncio.create_task(self._read_loop(), name=f"mcp-{self.name}")
        await self._initialize()
        self._healthy = True
        self._last_health_check = time.monotonic()

    async def stop(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
        if self._proc:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._proc.kill()
        self._healthy = False

    async def list_tools(self) -> list[ToolSpec]:
        return self._tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        return await self.circuit_breaker.call(
            retry_api_call,
            self._call_tool_raw,
            tool_name,
            arguments,
        )

    async def ping(self) -> bool:
        try:
            await asyncio.wait_for(
                self._send_request("ping", {}),
                timeout=self.config.timeout_ms / 1000,
            )
            self._healthy = True
            self._last_health_check = time.monotonic()
            return True
        except Exception:
            self._healthy = False
            return False

    @property
    def healthy(self) -> bool:
        return self._healthy

    # ---------------------------------------------------------------- private

    async def _initialize(self) -> None:
        """Send MCP initialize + tools/list."""
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "forge_agent", "version": "1.0.0"},
        })
        result = await self._send_request("tools/list", {})
        raw_tools = result.get("tools", [])
        self._tools = [
            ToolSpec(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {}),
            )
            for t in raw_tools
        ]

    async def _call_tool_raw(self, tool_name: str, arguments: dict) -> Any:
        result = await asyncio.wait_for(
            self._send_request("tools/call", {"name": tool_name, "arguments": arguments}),
            timeout=self.config.timeout_ms / 1000,
        )
        return result.get("content", result)

    async def _send_request(self, method: str, params: dict) -> dict:
        import json
        async with self._lock:
            self._msg_id += 1
            msg_id = self._msg_id

        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = fut

        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params,
        }) + "\n"

        assert self._proc and self._proc.stdin
        self._proc.stdin.write(payload.encode())
        await self._proc.stdin.drain()

        try:
            response = await asyncio.wait_for(fut, timeout=self.config.timeout_ms / 1000)
        finally:
            self._pending.pop(msg_id, None)

        if "error" in response:
            raise MCPConnectionError(f"MCP error from {self.name}: {response['error']}")
        return response.get("result", {})

    async def _read_loop(self) -> None:
        import json
        assert self._proc and self._proc.stdout
        while True:
            try:
                line = await self._proc.stdout.readline()
                if not line:
                    break
                msg = json.loads(line.decode())
                msg_id = msg.get("id")
                if msg_id and msg_id in self._pending:
                    fut = self._pending[msg_id]
                    if not fut.done():
                        fut.set_result(msg)
            except asyncio.CancelledError:
                break
            except Exception:
                pass


class MCPManager:
    """Manages all MCP servers; provides unified tool routing.

    Dispatch order: CLI first (CliDispatcher), MCP second.
    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._servers: dict[str, MCPServer] = {}
        self._tool_to_server: dict[str, str] = {}
        self._config_path = config_path or (
            Path(__file__).parent.parent / "config" / "servers.yaml"
        )
        self._health_task: asyncio.Task | None = None
        self._cli = CliDispatcher()

    async def start(self) -> None:
        configs = self._load_config()
        for cfg in configs:
            srv = MCPServer(cfg)
            self._servers[cfg.name] = srv
            try:
                await srv.start()
                for tool in await srv.list_tools():
                    self._tool_to_server[tool.name] = cfg.name
            except Exception as exc:
                print(f"[MCPManager] WARNING: failed to start server {cfg.name!r}: {exc}")

        self._health_task = asyncio.create_task(self._health_monitor(), name="mcp-health")

    async def stop(self) -> None:
        if self._health_task:
            self._health_task.cancel()
        for srv in self._servers.values():
            await srv.stop()

    async def list_all_tools(self) -> list[ToolSpec]:
        tools = []
        for srv in self._servers.values():
            if srv.healthy:
                tools.extend(await srv.list_tools())
        return tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        # ── 1. CLI path (primary) ──────────────────────────────────────────────
        result, handled = await self._cli.call(tool_name, arguments)
        if handled:
            return result

        # ── 2. MCP fallback ────────────────────────────────────────────────────
        server_name = self._tool_to_server.get(tool_name)
        if server_name is None:
            raise MCPConnectionError(
                f"No CLI handler or MCP server registered for tool {tool_name!r}. "
                f"CLI tools: {self._cli.registered_tools()}"
            )
        srv = self._servers[server_name]
        if not srv.healthy:
            raise MCPConnectionError(f"MCP server {server_name!r} is unhealthy")
        return await srv.call_tool(tool_name, arguments)

    def healthy_servers(self) -> list[str]:
        return [name for name, srv in self._servers.items() if srv.healthy]

    def all_servers(self) -> list[str]:
        return list(self._servers.keys())

    # ---------------------------------------------------------------- private

    def _load_config(self) -> list[ServerConfig]:
        path = Path(self._config_path)
        if not path.exists():
            return []
        with path.open() as f:
            data = yaml.safe_load(f) or {}
        servers_data = data.get("servers", {})
        configs = []
        for name, spec in servers_data.items():
            configs.append(ServerConfig(
                name=name,
                command=spec.get("command", []),
                timeout_ms=spec.get("timeout_ms", 5000),
                health_check_interval_s=spec.get("health_check_interval_s", 30.0),
                env=spec.get("env", {}),
            ))
        return configs

    async def _health_monitor(self) -> None:
        while True:
            try:
                await asyncio.sleep(5.0)
                for srv in self._servers.values():
                    elapsed = time.monotonic() - srv._last_health_check
                    if elapsed >= srv.config.health_check_interval_s:
                        await srv.ping()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

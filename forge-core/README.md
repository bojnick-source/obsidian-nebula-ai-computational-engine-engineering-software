# forge-core

C++ orchestration spine for FORGE. Implements: blackboard, model router, orchestrator, A2A transport, MCP client, verification orchestration, and JSONL logging.

## Structure

```
include/forge/          # Public headers (grouped by subsystem)
  app/                  # Application entry point, startup, shutdown
  config/               # Config loader, YAML parsing, schema versions
  routing/              # Model router, provider adapters, health monitor
  blackboard/           # Typed shared state, validators, concurrency guard
  orchestration/        # Orchestrator, task graph, dependency DAG, dispatch
  a2a/                  # A2A transport (gRPC + local shim), debate lifecycle
  mcp/                  # MCP client, tool invocation, result envelope
  verification/         # Verifier interfaces (structural, adversarial, provenance...)
  logging/              # JSONL logger, trace context, error codes, metrics
  common/               # IDs, result type, time utils, enums
src/                    # Implementation (mirrors include/forge/)
proto/                  # Protobuf definitions (A2A protocol)
configs/                # Runtime YAML configs
tests/                  # Unit, integration, fixtures, smoke
```

## Build

```bash
cmake -S . -B build -DFORGE_BUILD_TESTS=ON
cmake --build build
ctest --test-dir build
```

## Status

Planning scaffold — headers defined, implementations pending.

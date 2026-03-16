cmake_minimum_required(VERSION 3.20)
project(FORGE VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── Build options ─────────────────────────────────────────────────────────────
option(FORGE_BUILD_TESTS  "Build test targets"        ON)
option(FORGE_ENABLE_ASAN  "Enable AddressSanitizer"   OFF)
option(FORGE_ENABLE_TSAN  "Enable ThreadSanitizer"    OFF)

# ── Compiler flags ─────────────────────────────────────────────────────────────
add_compile_options(-Wall -Wextra -Wpedantic)

if(FORGE_ENABLE_ASAN)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

if(FORGE_ENABLE_TSAN)
    add_compile_options(-fsanitize=thread)
    add_link_options(-fsanitize=thread)
endif()

# ── Optional dependencies (uncomment when libraries are installed) ─────────────
# find_package(Protobuf REQUIRED)
# find_package(gRPC REQUIRED)
# find_package(yaml-cpp REQUIRED)
# find_package(nlohmann_json REQUIRED)
# find_package(spdlog REQUIRED)
# find_package(cppzmq REQUIRED)  # ZeroMQ C++ bindings (for event bus)

# ── forge_common ──────────────────────────────────────────────────────────────
# UUID generation, ISO-8601 timestamps, enum to_string, Result<T>.
# Language: C++  Role: shared primitives used by all other forge-core targets
add_library(forge_common STATIC
    forge-core/src/common/ids.cpp
    forge-core/src/common/time.cpp
    forge-core/src/common/enums.cpp
)
target_include_directories(forge_common PUBLIC
    forge-core/include
)

# ── forge_blackboard ──────────────────────────────────────────────────────────
# Thread-safe shared state for one task execution.  Latency target: < 50 ms.
# Language: C++  Role: blackboard (shared read/write state across agents)
add_library(forge_blackboard STATIC
    forge-core/src/blackboard/concurrency_guard.cpp
    forge-core/src/blackboard/blackboard.cpp
)
target_include_directories(forge_blackboard PUBLIC
    forge-core/include
)
target_link_libraries(forge_blackboard PUBLIC forge_common)

# ── forge_routing ─────────────────────────────────────────────────────────────
# Health-aware LLM provider selection.  Latency target: < 100 ms.
# Language: C++  Role: model router
add_library(forge_routing STATIC
    forge-core/src/routing/model_router.cpp
)
target_include_directories(forge_routing PUBLIC
    forge-core/include
)
target_link_libraries(forge_routing PUBLIC forge_common)

# ── forge_orchestration ───────────────────────────────────────────────────────
# 9-phase core loop + TaskGraph DAG.
# Language: C++  Role: orchestration, agent lifecycle
add_library(forge_orchestration STATIC
    forge-core/src/orchestration/task_graph.cpp
    forge-core/src/orchestration/orchestrator.cpp
)
target_include_directories(forge_orchestration PUBLIC
    forge-core/include
)
target_link_libraries(forge_orchestration PUBLIC
    forge_common
    forge_blackboard
)

# ── forge_logging ─────────────────────────────────────────────────────────────
# JSONL structured logger (mirrors Python AgentLogger format for unified ingest).
# Language: C++  Role: observability
add_library(forge_logging STATIC
    forge-core/src/logging/jsonl_logger.cpp
)
target_include_directories(forge_logging PUBLIC
    forge-core/include
)
target_link_libraries(forge_logging PUBLIC forge_common)

# ── forge_events ──────────────────────────────────────────────────────────────
# Event bus emitter (JSONL now; ZMQ PUB when libzmq is linked).
# Language: C++  Role: event bus / observability pipeline
add_library(forge_events STATIC
    forge-core/src/events/event_emitter.cpp
)
target_include_directories(forge_events PUBLIC
    forge-core/include
)
# Uncomment when libzmq is available:
# target_link_libraries(forge_events PUBLIC forge_common libzmq)
target_link_libraries(forge_events PUBLIC forge_common)

# ── forge_core (aggregate interface target) ───────────────────────────────────
# Link this single target to get the full C++ core runtime.
add_library(forge_core INTERFACE)
target_link_libraries(forge_core INTERFACE
    forge_common
    forge_blackboard
    forge_routing
    forge_orchestration
    forge_logging
    forge_events
)

# ── Tests ─────────────────────────────────────────────────────────────────────
if(FORGE_BUILD_TESTS)
    enable_testing()
    # add_subdirectory(forge-tests)  # C++ unit tests (planned)
endif()

message(STATUS "FORGE v${PROJECT_VERSION} — polyglot core configured")
message(STATUS "  C++ targets  : forge_common forge_blackboard forge_routing")
message(STATUS "               : forge_orchestration forge_logging forge_events")
message(STATUS "  Python layer : forge_agent/ (MCP, vault, specialists)")
message(STATUS "  MATLAB layer : forge-tools/matlab-wrappers/ (FreeTO, Swan)")
message(STATUS "  GPU layer    : forge-gpu/ (PhysX 5.6, Warp, Newton)")

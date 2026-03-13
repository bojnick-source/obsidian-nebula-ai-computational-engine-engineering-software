cmake_minimum_required(VERSION 3.20)
project(FORGE VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── Build options ────────────────────────────────────────────────────────────
option(FORGE_BUILD_TESTS "Build test targets" ON)
option(FORGE_ENABLE_ASAN  "Enable AddressSanitizer" OFF)
option(FORGE_ENABLE_TSAN  "Enable ThreadSanitizer" OFF)

# ── Compiler flags ────────────────────────────────────────────────────────────
add_compile_options(-Wall -Wextra -Wpedantic)

if(FORGE_ENABLE_ASAN)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

if(FORGE_ENABLE_TSAN)
    add_compile_options(-fsanitize=thread)
    add_link_options(-fsanitize=thread)
endif()

# ── Dependencies (placeholder — populate as libraries are added) ──────────────
# find_package(Protobuf REQUIRED)
# find_package(gRPC REQUIRED)
# find_package(yaml-cpp REQUIRED)
# find_package(nlohmann_json REQUIRED)
# find_package(spdlog REQUIRED)
# find_package(cppzmq REQUIRED)  # ZeroMQ C++ bindings (for event bus)

# ── forge-core: events subsystem ─────────────────────────────────────────────
add_library(forge_events STATIC
    forge-core/src/events/event_emitter.cpp
)
target_include_directories(forge_events PUBLIC
    forge-core/include
)
# When ZMQ is available, link it:
# target_link_libraries(forge_events PUBLIC libzmq)

# ── forge-core: solver subsystem (C++ accuracy layer) ────────────────────────
# Polyglot policy: C++20 float64 for deterministic, accuracy-critical computation.
# Python orchestration layer: forge-solver/ (atmosphere.py, bemt.py, fea.py,
#   topology.py, smart_fuselage.py)
add_library(forge_solver_core STATIC
    forge-core/src/solver/fea_linear.cpp
    forge-core/src/solver/bemt_core.cpp
    forge-core/src/solver/fuselage_aero.cpp
)
target_include_directories(forge_solver_core PUBLIC
    forge-core/include
)
set_target_properties(forge_solver_core PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
)
# Require strict IEEE 754 — no fast-math that could alter solver determinism
target_compile_options(forge_solver_core PRIVATE
    -fno-fast-math
    -Wall -Wextra -Wpedantic
)

# ── forge-core library ────────────────────────────────────────────────────────
# Populated when source files exist
# add_subdirectory(forge-core)

# ── Tests ─────────────────────────────────────────────────────────────────────
if(FORGE_BUILD_TESTS)
    enable_testing()
    # add_subdirectory(forge-tests)
endif()

message(STATUS "FORGE v${PROJECT_VERSION} — polyglot: C++ solver core + Python orchestration")

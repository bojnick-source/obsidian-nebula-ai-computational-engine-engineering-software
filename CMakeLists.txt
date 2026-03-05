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

# ── forge-core library ────────────────────────────────────────────────────────
# Populated when source files exist
# add_subdirectory(forge-core)

# ── Tests ─────────────────────────────────────────────────────────────────────
if(FORGE_BUILD_TESTS)
    enable_testing()
    # add_subdirectory(forge-tests)
endif()

message(STATUS "FORGE v${PROJECT_VERSION} — planning scaffold (build system placeholder)")

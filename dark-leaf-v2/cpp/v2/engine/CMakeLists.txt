cmake_minimum_required(VERSION 3.20)
project(v2_engine VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---------------------------------------------------------------------------
# v2 baseline physics library
# ---------------------------------------------------------------------------
add_library(v2_physics STATIC
    src/physics/baseline/hover_power_model.cpp
    src/physics/baseline/disk_area_calculator.cpp
)
target_include_directories(v2_physics PUBLIC src)

# ---------------------------------------------------------------------------
# Legacy 4-1 lift:: physics library
# ---------------------------------------------------------------------------
add_library(lift_legacy STATIC
    src/legacy_4_1/engine/physics/hover_momentum.cpp
    src/legacy_4_1/engine/physics/disk_area.cpp
)
target_include_directories(lift_legacy PUBLIC src/legacy_4_1)

# ---------------------------------------------------------------------------
# v2_engine_cli — JSON subprocess bridge consumed by v2_engine.py
# ---------------------------------------------------------------------------
add_executable(v2_engine_cli src/main.cpp)
target_include_directories(v2_engine_cli PRIVATE src src/legacy_4_1)
target_link_libraries(v2_engine_cli PRIVATE v2_physics lift_legacy)

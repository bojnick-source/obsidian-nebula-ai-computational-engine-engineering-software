#pragma once
/*
================================================================================
Legacy 4-1 Engine Core — Error Types
FILE: engine/core/errors.hpp
================================================================================
*/

#include <stdexcept>
#include <string>

namespace lift {

/// Thrown for invalid physics inputs (non-positive thrust, bad FM, etc.)
struct ValidationError : std::runtime_error {
    explicit ValidationError(const std::string& msg)
        : std::runtime_error(msg) {}
};

} // namespace lift

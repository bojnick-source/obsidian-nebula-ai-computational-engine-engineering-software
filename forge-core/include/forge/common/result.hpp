#pragma once
#include <string>
#include <variant>
#include <optional>

namespace forge::common {

/// Error with a code and human-readable detail.
struct Error {
    std::string code;    ///< e.g., "ERR_CONTRACT_VIOLATION"
    std::string detail;  ///< human-readable message
};

/// Result<T>: either a value T or an Error.
/// Use .ok() to check, .value() to get T, .error() to get Error.
template<typename T>
class Result {
public:
    static Result<T> ok(T value)      { return Result<T>{std::move(value)}; }
    static Result<T> err(Error error) { return Result<T>{std::move(error)}; }

    bool has_value() const noexcept { return std::holds_alternative<T>(data_); }
    bool has_error() const noexcept { return std::holds_alternative<Error>(data_); }

    T&           value()       { return std::get<T>(data_); }
    const T&     value() const { return std::get<T>(data_); }
    Error&       error()       { return std::get<Error>(data_); }
    const Error& error() const { return std::get<Error>(data_); }

    explicit operator bool() const noexcept { return has_value(); }

private:
    explicit Result(T v)     : data_(std::move(v)) {}
    explicit Result(Error e) : data_(std::move(e)) {}

    std::variant<T, Error> data_;
};

/// Convenience alias for void results.
using VoidResult = Result<std::monostate>;
inline VoidResult ok_void() { return VoidResult::ok(std::monostate{}); }

} // namespace forge::common

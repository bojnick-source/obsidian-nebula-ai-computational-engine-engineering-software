/*
================================================================================
v2_engine_cli — JSON subprocess bridge
FILE: src/main.cpp

Usage:
  v2_engine_cli --canonical-input <json_string> [--artifact-root <path>] [--no-write]

Supported models (set "model" key in JSON input):
  hover_power_v2      — v2 baseline (v2::physics::baseline)
  hover_power_legacy  — legacy 4-1 lift:: namespace

Input JSON keys:
  model            string   required
  thrust_N         double   required  [N]
  rotor_radius_m   double   required  [m]
  rotor_count      int      default 1
  rho_kg_m3        double   default 1.225 [kg/m³]
  hover_FM         double   default 0.70
  induced_k        double   default 1.15
  reserve_mult     double   default 1.0 (1.0 = no reserve sizing)
  is_coaxial       bool     default false
  coax_pairs       int      default 0
  has_shroud       bool     default false
  shroud_inner_m   double   default 0.0

Output JSON (stdout):
  model, thrust_N, A_single_m2, A_total_m2, effective_disk_count,
  disk_loading_N_per_m2, P_induced_ideal_W, P_induced_W, P_total_W, rho_used, FM_used
================================================================================
*/

#include "physics/baseline/disk_area_calculator.hpp"
#include "physics/baseline/hover_power_model.hpp"

#include "engine/physics/disk_area.hpp"
#include "engine/physics/hover_momentum.hpp"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>
#include <stdexcept>
#include <string>

// ---------------------------------------------------------------------------
// Minimal JSON helpers — no external deps
// ---------------------------------------------------------------------------

static std::string json_str_value(const std::string& json, const std::string& key,
                                   const std::string& def = "") {
    // Finds "key": "value" and returns value
    const std::string needle = "\"" + key + "\"";
    auto pos = json.find(needle);
    if (pos == std::string::npos) return def;
    pos = json.find(':', pos + needle.size());
    if (pos == std::string::npos) return def;
    pos = json.find('"', pos + 1);
    if (pos == std::string::npos) return def;
    auto end = json.find('"', pos + 1);
    if (end == std::string::npos) return def;
    return json.substr(pos + 1, end - pos - 1);
}

static double json_dbl_value(const std::string& json, const std::string& key, double def) {
    // Finds "key": <number>
    const std::string needle = "\"" + key + "\"";
    auto pos = json.find(needle);
    if (pos == std::string::npos) return def;
    pos = json.find(':', pos + needle.size());
    if (pos == std::string::npos) return def;
    // skip whitespace
    ++pos;
    while (pos < json.size() && (json[pos] == ' ' || json[pos] == '\t' ||
                                  json[pos] == '\n' || json[pos] == '\r'))
        ++pos;
    if (pos >= json.size()) return def;
    char* endptr = nullptr;
    double val = std::strtod(json.c_str() + pos, &endptr);
    if (endptr == json.c_str() + pos) return def;
    return val;
}

static bool json_bool_value(const std::string& json, const std::string& key, bool def) {
    const std::string needle = "\"" + key + "\"";
    auto pos = json.find(needle);
    if (pos == std::string::npos) return def;
    pos = json.find(':', pos + needle.size());
    if (pos == std::string::npos) return def;
    ++pos;
    while (pos < json.size() && (json[pos] == ' ' || json[pos] == '\t' ||
                                  json[pos] == '\n' || json[pos] == '\r'))
        ++pos;
    if (json.compare(pos, 4, "true") == 0) return true;
    if (json.compare(pos, 5, "false") == 0) return false;
    return def;
}

// ---------------------------------------------------------------------------
// Output helpers
// ---------------------------------------------------------------------------

static std::string dbl(double v) {
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%.6g", v);
    return buf;
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main(int argc, char* argv[]) {
    std::string canonical_input;
    std::string artifact_root;
    bool        no_write = false;

    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--canonical-input") == 0 && i + 1 < argc) {
            canonical_input = argv[++i];
        } else if (std::strcmp(argv[i], "--artifact-root") == 0 && i + 1 < argc) {
            artifact_root = argv[++i];
        } else if (std::strcmp(argv[i], "--no-write") == 0) {
            no_write = true;
        }
    }

    if (canonical_input.empty()) {
        std::fprintf(stderr, "{\"error\": \"--canonical-input is required\"}\n");
        return 1;
    }

    try {
        const std::string& j = canonical_input;
        const std::string model = json_str_value(j, "model", "hover_power_v2");

        const double thrust_N      = json_dbl_value(j, "thrust_N",      -1.0);
        const double rotor_radius  = json_dbl_value(j, "rotor_radius_m", -1.0);
        const double rotor_count   = json_dbl_value(j, "rotor_count",     1.0);
        const double rho           = json_dbl_value(j, "rho_kg_m3",      1.225);
        const double hover_FM      = json_dbl_value(j, "hover_FM",        0.70);
        const double induced_k     = json_dbl_value(j, "induced_k",       1.15);
        const double reserve_mult  = json_dbl_value(j, "reserve_mult",    1.0);
        const bool   is_coaxial    = json_bool_value(j, "is_coaxial",     false);
        const int    coax_pairs    = static_cast<int>(json_dbl_value(j, "coax_pairs", 0.0));
        const bool   has_shroud    = json_bool_value(j, "has_shroud",     false);
        const double shroud_inner  = json_dbl_value(j, "shroud_inner_m",  0.0);

        if (thrust_N <= 0.0)
            throw std::invalid_argument("thrust_N must be > 0");
        if (rotor_radius <= 0.0)
            throw std::invalid_argument("rotor_radius_m must be > 0");

        if (model == "hover_power_v2") {
            // ---- Disk area ----
            v2::physics::RotorGeometry geom;
            geom.rotor_radius_m        = rotor_radius;
            geom.rotor_count           = rotor_count;
            geom.is_coaxial            = is_coaxial;
            geom.coax_pairs            = coax_pairs;
            geom.has_shroud            = has_shroud;
            geom.shroud_inner_radius_m = shroud_inner;

            v2::physics::baseline::DiskAreaCalculator da_calc;
            const auto da = da_calc.compute(geom);

            // ---- Power ----
            v2::physics::AtmosphereConditions atm;
            atm.rho_kg_m3 = rho;

            v2::physics::RotorPerformance perf;
            perf.hover_FM  = hover_FM;
            perf.induced_k = induced_k;

            v2::physics::baseline::HoverPowerModel hp_model;
            const auto hp = (reserve_mult > 1.0)
                ? hp_model.compute_power_sized(thrust_N, da.A_total_m2, atm, perf, reserve_mult)
                : hp_model.compute_power(thrust_N, da.A_total_m2, atm, perf);

            std::printf(
                "{"
                "\"model\":\"hover_power_v2\","
                "\"thrust_N\":%s,"
                "\"A_single_m2\":%s,"
                "\"A_total_m2\":%s,"
                "\"effective_disk_count\":%d,"
                "\"disk_loading_N_per_m2\":%s,"
                "\"P_induced_ideal_W\":%s,"
                "\"P_induced_W\":%s,"
                "\"P_total_W\":%s,"
                "\"rho_used_kg_m3\":%s,"
                "\"FM_used\":%s,"
                "\"notes\":\"%s\""
                "}\n",
                dbl(hp.thrust_N).c_str(),
                dbl(da.A_single_m2).c_str(),
                dbl(da.A_total_m2).c_str(),
                da.effective_disk_count,
                dbl(hp.disk_loading_N_per_m2).c_str(),
                dbl(hp.P_induced_ideal_W).c_str(),
                dbl(hp.P_induced_W).c_str(),
                dbl(hp.P_total_W).c_str(),
                dbl(hp.rho_used_kg_m3).c_str(),
                dbl(hp.FM_used).c_str(),
                da.notes.c_str());

        } else if (model == "hover_power_legacy") {
            // ---- Legacy lift:: path ----
            lift::Design d;
            d.rotor_radius_m        = rotor_radius;
            d.rotor_count           = static_cast<int>(rotor_count);
            d.is_coaxial            = is_coaxial;
            d.coax_pairs            = coax_pairs;
            d.has_shroud            = has_shroud;
            d.shroud_inner_radius_m = shroud_inner;

            const auto da = lift::compute_effective_disk_area(d);

            lift::EvalSettings s;
            s.atmosphere.rho_kg_m3 = rho;
            s.rotor.hover_FM       = hover_FM;
            s.rotor.induced_k      = induced_k;

            const auto hp = (reserve_mult > 1.0)
                ? lift::hover_momentum_power_sized(thrust_N, da.A_total_m2, s, reserve_mult)
                : lift::hover_momentum_power(thrust_N, da.A_total_m2, s);

            std::printf(
                "{"
                "\"model\":\"hover_power_legacy\","
                "\"thrust_N\":%s,"
                "\"A_single_m2\":%s,"
                "\"A_total_m2\":%s,"
                "\"effective_disk_count\":%d,"
                "\"disk_loading_N_per_m2\":%s,"
                "\"P_induced_ideal_W\":%s,"
                "\"P_induced_W\":%s,"
                "\"P_total_W\":%s,"
                "\"rho_used_kg_m3\":%s,"
                "\"FM_used\":%s,"
                "\"notes\":\"%s\""
                "}\n",
                dbl(hp.thrust_N).c_str(),
                dbl(da.A_single_m2).c_str(),
                dbl(da.A_total_m2).c_str(),
                da.effective_disk_count,
                dbl(hp.disk_loading_N_per_m2).c_str(),
                dbl(hp.P_induced_ideal_W).c_str(),
                dbl(hp.P_induced_W).c_str(),
                dbl(hp.P_total_W).c_str(),
                dbl(hp.rho_used).c_str(),
                dbl(hp.FM_used).c_str(),
                da.notes.c_str());

        } else {
            std::fprintf(stderr, "{\"error\": \"unknown model: %s\"}\n", model.c_str());
            return 1;
        }

    } catch (const std::exception& ex) {
        std::fprintf(stderr, "{\"error\": \"%s\"}\n", ex.what());
        return 1;
    }

    return 0;
}

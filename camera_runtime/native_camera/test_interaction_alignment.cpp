#include "interaction_alignment.h"
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>

namespace {
apex_view::Stats bridge_stats{};
int bridge_status = 0;
int get_stats(apex_view::Stats* stats) {
    *stats = bridge_stats;
    return bridge_status;
}
bool check(bool condition, const char* name) {
    if (!condition) std::cerr << "FAIL: " << name << '\n';
    return condition;
}
}

int main() {
    // This is the real measured mismatch, with a signed shoulder displacement.
    apex_interaction::Sample sample{{110770.179, -153943.301, 20663.374},
                           {336.783, 80.483, 0}, {110770.179, -153943.301, 20592.374}};
    apex_interaction::CameraView right{{110681.916, -154177.048, 20746.320}, {-23.218, 80.483, 0}};
    apex_interaction::CameraView left{{110777.384, -154193.053, 20746.320}, {-23.218, 80.483, 0}};
    bool ok = true;
    for (const auto& view : {right, left}) {
        std::array<unsigned char, 256> output{};
        output.fill(0xA5);
        std::memcpy(output.data(), &sample, sizeof(sample));
        const float extended_loot_distance = 660.0F;
        std::memcpy(output.data() + 0xC8, &extended_loot_distance, sizeof(extended_loot_distance));
        const auto baseline = output;
        const bool changed = apex_interaction::align_output(output.data(), sample, view);
        ok &= check(changed, "measured shoulder ray must be replaced");
        apex_interaction::CameraView corrected{};
        std::memcpy(&corrected, output.data(), sizeof(corrected));
        const double radians = 0.017453292519943295;
        const double pitch = view.rotation[0] * radians, yaw = view.rotation[1] * radians;
        const double forward[] = {std::cos(pitch) * std::cos(yaw),
                                  std::cos(pitch) * std::sin(yaw), std::sin(pitch)};
        double depth = 0, shift_depth = 0;
        for (int i = 0; i < 3; ++i) {
            depth += (corrected.origin[i] - view.origin[i]) * forward[i];
            shift_depth += (corrected.origin[i] - sample.origin[i]) * forward[i];
        }
        ok &= check(std::abs(shift_depth) < 1e-8, "preserve original start depth and segment reach");
        for (int i = 0; i < 3; ++i) {
            ok &= check(std::abs(corrected.origin[i] - view.origin[i] - depth * forward[i]) < 1e-8,
                        "corrected interaction must lie on the camera center ray");
        }
        ok &= check(std::memcmp(corrected.rotation, view.rotation, sizeof(view.rotation)) == 0,
                    "direction must match the rendered camera");
        ok &= check(std::memcmp(output.data() + sizeof(view), baseline.data() + sizeof(view),
                                output.size() - sizeof(view)) == 0,
                    "anchor, range and all remaining metadata must stay unchanged");
    }
    auto output = sample;
    auto invalid = right;
    invalid.origin[1] = std::numeric_limits<double>::quiet_NaN();
    ok &= check(!apex_interaction::align_output(&output, sample, invalid), "reject NaN");
    invalid = right;
    invalid.origin[0] += 10000;
    ok &= check(!apex_interaction::align_output(&output, sample, invalid), "reject distant camera");
    ok &= check(std::memcmp(&output, &sample, sizeof(sample)) == 0, "refusal cannot write");
    ok &= check(!apex_interaction::align_output(nullptr, sample, right), "reject null output");
    std::array<unsigned char, 0x500> pc{};
    std::array<unsigned char, 0x1980> manager{};
    apex_interaction::Config config{apex_interaction::abi, 0, reinterpret_cast<uint64_t>(pc.data()),
                            0x20000, reinterpret_cast<uint64_t>(manager.data()), 0};
    std::memcpy(pc.data() + apex_interaction::pawn_offset, &config.pawn, sizeof(config.pawn));
    std::memcpy(pc.data() + apex_interaction::manager_offset, &config.manager, sizeof(config.manager));
    std::memcpy(manager.data() + apex_interaction::cache_view_offset, &right, sizeof(right));
    const float timestamp = 10;
    std::memcpy(manager.data() + apex_interaction::cache_time_offset, &timestamp, sizeof(timestamp));
    apex_interaction::CameraView observed{};
    bridge_stats.active = 1;
    const float empty_timestamp = 0;
    std::memcpy(manager.data() + apex_interaction::cache_time_offset, &empty_timestamp, sizeof(empty_timestamp));
    ok &= check(apex_interaction::read_camera(config, get_stats, observed) == -1,
                "loading without a cached frame cannot write");
    std::memcpy(manager.data() + apex_interaction::cache_time_offset, &timestamp, sizeof(timestamp));
    ok &= check(apex_interaction::read_camera(config, get_stats, observed) == 1
                && std::memcmp(&observed, &right, sizeof(right)) == 0, "read cached render view");
    bridge_stats.suspended = 1;
    ok &= check(apex_interaction::read_camera(config, get_stats, observed) == 0,
                "ADS and vehicle suspension must bypass correction");
    bridge_stats.suspended = 0;
    bridge_stats.active = 0;
    ok &= check(apex_interaction::read_camera(config, get_stats, observed) == 0,
                "first person or disabled camera must bypass correction");
    bridge_stats.active = 1;
    config.pawn += 8;
    ok &= check(apex_interaction::read_camera(config, get_stats, observed) == 0, "reject changed pawn");
    config.pawn -= 8;
    config.manager = 0;
    ok &= check(apex_interaction::read_camera(config, get_stats, observed) == 0, "reject changed manager");
    bridge_status = 3;
    ok &= check(apex_interaction::read_camera(config, get_stats, observed) == -1, "reject failed camera bridge");
    std::cout << "RESULTAT: " << (ok ? "OK" : "ECHEC") << " - interaction ray alignment\n";
    return ok ? 0 : 1;
}

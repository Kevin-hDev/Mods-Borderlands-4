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
    // Measured on 2026-09-26: the game's eyes (the hunter plus 71 cm) and the camera on either shoulder.
    const apex_interaction::View eyes{{110770.179, -153943.301, 20663.374}, {336.783, 80.483, 1.5}};
    const apex_interaction::View right{{110681.916, -154177.048, 20746.320}, {-23.218, 80.483, 0}};
    const apex_interaction::View left{{110777.384, -154193.053, 20746.320}, {-23.218, 80.483, 0}};
    bool ok = true;
    for (const auto& camera : {right, left}) {
        apex_interaction::View aligned{};
        ok &= check(apex_interaction::align(eyes, camera, aligned), "measured shoulder eyes must be moved");
        const double radians = 0.017453292519943295;
        const double pitch = camera.rotation[0] * radians, yaw = camera.rotation[1] * radians;
        const double forward[] = {std::cos(pitch) * std::cos(yaw),
                                  std::cos(pitch) * std::sin(yaw), std::sin(pitch)};
        double depth = 0, shift_depth = 0;
        for (int i = 0; i < 3; ++i) {
            depth += (aligned.origin[i] - camera.origin[i]) * forward[i];
            shift_depth += (aligned.origin[i] - eyes.origin[i]) * forward[i];
        }
        ok &= check(std::abs(shift_depth) < 1e-8, "the eyes keep their depth, and a fixed-length line its reach");
        for (int i = 0; i < 3; ++i) {
            ok &= check(std::abs(aligned.origin[i] - camera.origin[i] - depth * forward[i]) < 1e-8,
                        "the eyes lie on the camera's center ray");
        }
        ok &= check(aligned.rotation[0] == camera.rotation[0] && aligned.rotation[1] == camera.rotation[1],
                    "the eyes look where the camera looks");
        ok &= check(aligned.rotation[2] == eyes.rotation[2], "the game's roll stays");
    }
    apex_interaction::View aligned = eyes;
    auto invalid = right;
    invalid.origin[1] = std::numeric_limits<double>::quiet_NaN();
    ok &= check(!apex_interaction::align(eyes, invalid, aligned), "reject NaN");
    invalid = right;
    invalid.origin[0] += 10000;
    ok &= check(!apex_interaction::align(eyes, invalid, aligned), "reject distant camera");
    invalid = right;
    invalid.rotation[1] += 180;
    ok &= check(!apex_interaction::align(eyes, invalid, aligned), "reject eyes behind the camera");
    auto strange = eyes;
    strange.rotation[0] = std::numeric_limits<double>::infinity();
    ok &= check(!apex_interaction::align(strange, right, aligned), "reject the game's undefined eyes");
    ok &= check(std::memcmp(&aligned, &eyes, sizeof(eyes)) == 0, "a refusal leaves the eyes as given");
    std::array<unsigned char, 0x500> pc{};
    std::array<unsigned char, 0x1980> manager{};
    apex_interaction::Config config{apex_interaction::abi, 0, reinterpret_cast<uint64_t>(pc.data()),
                            0x20000, reinterpret_cast<uint64_t>(manager.data()), 0};
    std::memcpy(pc.data() + apex_interaction::pawn_offset, &config.pawn, sizeof(config.pawn));
    std::memcpy(pc.data() + apex_interaction::manager_offset, &config.manager, sizeof(config.manager));
    std::memcpy(manager.data() + apex_interaction::cache_view_offset, &right, sizeof(right));
    const float timestamp = 10;
    apex_interaction::View observed{};
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
    bridge_stats.ads_effective = 1;
    ok &= check(apex_interaction::read_camera(config, get_stats, observed) == 1,
                "wall suspension keeps effective third-person ADS alignment");
    bridge_stats.ads_effective = 0;
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
    std::cout << "RESULTAT: " << (ok ? "OK" : "ECHEC") << " - the hunter's eyes on the camera ray\n";
    return ok ? 0 : 1;
}

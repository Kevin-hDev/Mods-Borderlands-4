#include "view_target_bridge.h"

#include <cmath>
#include <cstring>

namespace apex_view {
bool valid_config(const Config& config) {
    return config.abi == abi_version
        && config.duration_ms <= max_duration_ms
        && config.slot_index == update_slot
        && config.expected_rva > 0
        && config.expected_rva <= max_expected_rva
        && std::isfinite(config.right)
        && std::isfinite(config.up)
        && std::abs(config.right) <= max_offset
        && std::abs(config.up) <= max_offset;
}

bool shift_view(const Config& config, void* view_target, Stats& stats, bool write) {
    auto* bytes = static_cast<unsigned char*>(view_target);
    double location[3];
    std::memcpy(location, bytes + view_location_offset, sizeof(location));
    std::memcpy(&stats.yaw, bytes + view_yaw_offset, sizeof(stats.yaw));
    if (!std::isfinite(stats.yaw) || std::abs(stats.yaw) > max_yaw) {
        return false;
    }
    for (double coordinate : location) {
        if (!std::isfinite(coordinate) || std::abs(coordinate) > max_coordinate) {
            return false;
        }
    }
    std::memcpy(stats.before, location, sizeof(location));
    location[0] -= config.right * std::sin(stats.yaw * degrees_to_radians);
    location[1] += config.right * std::cos(stats.yaw * degrees_to_radians);
    location[2] += config.up;
    std::memcpy(stats.after, location, sizeof(location));
    if (write) {
        std::memcpy(bytes + view_location_offset, location, sizeof(location));
    }
    return true;
}
}

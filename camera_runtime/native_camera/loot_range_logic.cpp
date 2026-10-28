#include "loot_range_logic.h"
#include <cmath>
#include <cstring>

namespace apex_loot {
bool valid_distance(float distance) {
    return std::isfinite(distance) && distance >= min_distance && distance <= max_distance;
}

const void* prepare_override(const Addresses& build, uintptr_t caller, const void* original, float distance,
                             OverridePool& pool) {
    if (!valid_distance(distance) || (caller != build.pickup_primary_caller
                                     && caller != build.pickup_secondary_caller)) return original;
    // The validated pickup getter has no config; these two consumers accept the bounded copy.
    ConfigImage& output = pool.slots[pool.cursor++ % pool_size];
    std::memset(output.bytes, 0, config_size);
    output.bytes[custom_flag_offset] = 1;
    std::memcpy(output.bytes + custom_distance_offset, &distance, sizeof(distance));
    return &output;
}
}

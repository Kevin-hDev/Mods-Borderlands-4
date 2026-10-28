#pragma once
#include "generated_ads.h"
#include <cmath>
#include <cstring>

namespace apex_framing {
inline bool within(uint32_t size, uint32_t offset, size_t bytes) {
    return size && size <= apex_ads::MAX_TYPE_BYTES && offset <= size && bytes <= size - offset;
}
// Reflected layout and live addresses only: never retain a prior frame's position.
template<class Layout> bool read_body(const Layout& config, double (&output)[3]) {
    if (!config.actor || !config.root
        || !within(config.actor_size, config.root_offset, sizeof(uintptr_t))
        || !within(config.actor_size, config.capsule_offset, sizeof(uintptr_t))
        || !within(config.root_size, config.parent_offset, sizeof(uintptr_t))
        || !within(config.root_size, config.location_offset, sizeof(output))
        || !within(config.root_size, apex_ads::OBJECT_OUTER_OFFSET, sizeof(uintptr_t))) return false;
    const auto* actor = reinterpret_cast<const unsigned char*>(config.actor);
    const auto* root = reinterpret_cast<const unsigned char*>(config.root);
    uintptr_t actual_root{}, capsule{}, parent{}, owner{};
    std::memcpy(&actual_root, actor + config.root_offset, sizeof(actual_root));
    std::memcpy(&capsule, actor + config.capsule_offset, sizeof(capsule));
    std::memcpy(&parent, root + config.parent_offset, sizeof(parent));
    std::memcpy(&owner, root + apex_ads::OBJECT_OUTER_OFFSET, sizeof(owner));
    if (actual_root != config.root || capsule != config.root || parent || owner != config.actor) return false;
    double current[3]{};
    std::memcpy(current, root + config.location_offset, sizeof(current));
    for (double value : current) if (!std::isfinite(value)) return false;
    std::memcpy(output, current, sizeof(output));
    return true;
}
}

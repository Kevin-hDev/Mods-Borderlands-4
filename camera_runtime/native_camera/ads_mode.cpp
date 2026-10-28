#include "ads_mode.h"
#include "ads_memory.h"
#include <cmath>

namespace apex_ads {
bool read_framing_mode(void* manager, uint64_t third_person_name, ModeSnapshot& output) {
    output = {};
    const auto address = reinterpret_cast<uintptr_t>(manager);
    uint64_t name{};
    uintptr_t mode{};
    float remaining{};
    uint8_t transitioning{};
    if (!third_person_name || !read_memory(address, MANAGER_MODE_OFFSET, name)
            || name != third_person_name || !read_memory(address, MANAGER_MODE_OBJECT_OFFSET, mode)
            || !read_memory(mode, MODE_BLEND_REMAINING_OFFSET, remaining)
            || !std::isfinite(remaining) || remaining < 0.0f
            || !read_memory(mode, MODE_TRANSITION_FLAG_OFFSET, transitioning) || transitioning > 1) return false;
    output = {name, mode, remaining == 0.0f && !transitioning};
    return true;
}
bool read_mode(void* manager, uint64_t third_person_name, ModeSnapshot& output) {
    ModeSnapshot current{};
    output = {};
    if (!read_framing_mode(manager, third_person_name, current) || !current.stable) return false;
    output = current;
    return true;
}
}

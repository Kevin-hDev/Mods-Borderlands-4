#include "ads_paths.h"
#include "camera_memory.h"
#include <cmath>
#include <cstring>

namespace {
bool readable(uintptr_t pointer, uint32_t size, uint32_t minimum) {
    return pointer >= apex_ads::MIN_POINTER && pointer % sizeof(void*) == 0
        && size >= minimum && size <= apex_ads::MAX_TYPE_BYTES
        && apex_camera::memory_access(reinterpret_cast<void*>(pointer), size);
}

uintptr_t pointer_at(uintptr_t base, size_t offset) {
    uintptr_t value{};
    std::memcpy(&value, reinterpret_cast<void*>(base + offset), sizeof(value));
    return value;
}
}

namespace apex_ads {
int read_paths(const Config& config, Sample& output, ZoomScale zoom, Crosshair crosshair) {
    output = {};
    if (config.abi != ADS_ABI || config.reserved || !zoom || !crosshair
        || !readable(config.state, config.state_size, static_cast<uint32_t>(STATE_MIN_SIZE))
        || !readable(config.inputs, config.inputs_size, static_cast<uint32_t>(INPUTS_MIN_SIZE))
        || !readable(config.controller, config.controller_size, static_cast<uint32_t>(CONTROLLER_MIN_SIZE))
        || (config.weapon && !readable(config.weapon, config.weapon_size, static_cast<uint32_t>(WEAPON_MIN_SIZE)))
        || (!config.weapon && config.weapon_size)
        || pointer_at(config.state, STATE_INPUTS_OFFSET) != config.inputs
        // Controller is at 0xe8 (live SDK metadata); ZoomFOV reads a different
        // reference at 0xe0. Do not require that camera target to be the controller.
        || pointer_at(config.inputs, INPUTS_CONTROLLER_OFFSET) != config.controller) return 1;

    // Native ZoomFOV::GetScale reads only this factor from its behavior argument.
    // Reuse its weapon-specific transition curve, not a second interpolation.
    alignas(16) unsigned char behavior[0x20]{};
    const float base_scale = 1.0f;
    std::memcpy(behavior + 0x18, &base_scale, sizeof(base_scale));
    const float factor = zoom(behavior, nullptr, reinterpret_cast<void*>(config.state));
    if (!std::isfinite(factor) || factor <= 0.0f || factor > MAX_ZOOM_SCALE) return 2;
    const bool requested = config.weapon && crosshair(reinterpret_cast<void*>(config.weapon));
    output = {factor, requested ? 1U : 0U, config.weapon ? 1U : 0U, 0};
    return 0;
}
}

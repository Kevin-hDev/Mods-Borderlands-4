#include "ads_view.h"
#include "ads_memory.h"
#include "view_performance.h"
#include <cmath>
#include <limits>

namespace {
bool no_crosshair_read(void*) { return false; }
bool sample_zoom(const apex_ads::Ticket& ticket, apex_ads::PathsSample& output) {
    __try {
        return apex_ads::read_paths(ticket.context.paths, output, ticket.zoom, &no_crosshair_read) == 0;
    } __except(GetExceptionCode() == EXCEPTION_ACCESS_VIOLATION
                   ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) {
        return false;
    }
}
bool store_fov(void* view, float value) {
    auto* target = static_cast<unsigned char*>(view) + apex_ads::FOV_OFFSET;
    if (!apex_camera::memory_access(target, sizeof(value), true)) return false;
    __try {
        std::memcpy(target, &value, sizeof(value));
        return true;
    } __except(EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}
}

namespace apex_ads {
float zoom_fov(float base, float scale) {
    if (!std::isfinite(base) || !(base > 0.0f && base < 180.0f)
            || !std::isfinite(scale) || !(scale > 0.0f && scale <= MAX_ZOOM_SCALE)) {
        return std::numeric_limits<float>::quiet_NaN();
    }
    const double radians = std::acos(-1.0) / 180.0;
    return static_cast<float>(2.0 * std::atan(std::tan(base * radians / 2.0) * scale) / radians);
}

bool update_view(State& state, void* manager, void* view, float delta, Update original) {
    apex_performance::Measurement timing(apex_performance::Stage::view, false);
    Ticket before{};
    const bool allowed = state.ticket(manager, before);
    timing.aiming = allowed;
    // Game exceptions are never swallowed; only our extra reads have fault guards.
    {
        apex_performance::Measurement original_timing(apex_performance::Stage::original, allowed);
        original(manager, view, delta);
    }
    if (!allowed || !state.current(before)) return false;
    float base{};
    PathsSample sample{};
    bool sampled = false;
    {
        apex_performance::Measurement zoom_timing(apex_performance::Stage::zoom, true);
        sampled = read_memory(reinterpret_cast<uintptr_t>(view), FOV_OFFSET, base)
            && sample_zoom(before, sample);
    }
    if (!sampled) {
        state.note_error(static_cast<uint32_t>(ERROR_CONTEXT));
        return false;
    }
    const float zoomed = zoom_fov(base, sample.zoom_scale);
    if (!std::isfinite(zoomed) || !(zoomed > 0.0f && zoomed < 180.0f)
            || !state.current(before) || !store_fov(view, zoomed)) return false;
    state.record_fov(before, base, zoomed, sample.zoom_scale);
    return true;
}
}

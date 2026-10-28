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

float optic_scale(float optic, bool known, float progress) {
    // Without the game's progress the optic is set at once, as it was until 2026-10-11.
    if (!known) return optic;
    // The last thousandth ends exactly at 1: the Python side lets a released aim go on a write at 1.
    if (progress <= 0.001f) return 1.0f;
    if (progress >= 1.0f) return optic;
    return 1.0f - (1.0f - optic) * progress;
}

bool update_view(State& state, void* manager, void* view, float delta, Update original, AimProgress progress) {
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
    // The player's optic replaces the weapon's own zoom (idea n° 6, Kevin 2026-10-09). It follows the game's aim
    // progress in and out, as the camera moving to the shoulder does: set at once, it made the view jump before that
    // move and pop back after it (Kevin, 2026-10-11: « ça casse tout le rendu des transitions »).
    const float optic = state.optic(before);
    float aim{};
    const bool known = optic > 0.0f && progress
        && progress(manager, reinterpret_cast<void*>(before.context.references[1].address), aim)
        && std::isfinite(aim) && aim >= 0.0f && aim <= 1.0f;
    const float scale = optic > 0.0f ? optic_scale(optic, known, aim) : sample.zoom_scale;
    const float zoomed = zoom_fov(base, scale);
    if (!std::isfinite(zoomed) || !(zoomed > 0.0f && zoomed < 180.0f)
            || !state.current(before) || !store_fov(view, zoomed)) return false;
    state.record_fov(before, base, zoomed, scale);
    return true;
}
}

#include "framing_view.h"
#include "framing_body.h"
#include "framing_math.h"
#include "ads_view.h"
#include "ads_memory.h"
#include "view_performance.h"
#include <cmath>

namespace {
struct BodyLayout {
    uintptr_t actor, root;
    uint32_t actor_size, root_size, root_offset, capsule_offset, location_offset, parent_offset;
};
bool finite(apex_framing::Vec3 value) {
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}
bool body(const apex_ads::FramingContext& context, apex_framing::Vec3& output) {
    const BodyLayout layout{context.references[1].address, context.references[3].address,
        context.actor_size, context.root_size, context.root_offset, context.capsule_offset,
        context.location_offset, context.parent_offset};
    if (!apex_camera::memory_access(reinterpret_cast<void*>(layout.actor), layout.actor_size)
        || !apex_camera::memory_access(reinterpret_cast<void*>(layout.root), layout.root_size)) return false;
    __try {
        double coordinates[3]{};
        if (!apex_framing::read_body(layout, coordinates)) return false;
        std::memcpy(&output, coordinates, sizeof(output));
        return true;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
}
namespace apex_framing {
Status apply(apex_ads::State& state, const apex_ads::FramingContext& context,
             void* manager, void* view, apex_view::Stats& stats,
             bool aiming, bool write, ProgressReader progress, bool* zoom_pending) {
    apex_performance::Measurement timing(apex_performance::Stage::framing, aiming);
    if (zoom_pending) *zoom_pending = false;
    if (!state.framing_allowed(context, manager)) return Status::context_unavailable;
    Vec3 anchor{}, rotation{};
    // An attached or expired body cannot qualify the optional view, including zoom.
    if (!body(context, anchor)) return Status::body_unavailable;
    float alpha = 0.0f, fov{};
    const bool unavailable = aiming && context.values[0] && (!progress
        || !progress(manager, reinterpret_cast<void*>(context.references[1].address), alpha)
        || !std::isfinite(alpha) || alpha < 0 || alpha > 1);
    // A weapon read controls only extra FOV; valid body framing remains independent.
    if (unavailable) alpha = 0.0f;
    const auto pointer = reinterpret_cast<uintptr_t>(view);
    if (!apex_ads::read_memory(pointer, apex_view::view_rotation_offset, rotation)
        || !apex_ads::read_memory(pointer, apex_ads::FOV_OFFSET, fov)) return Status::reference_unavailable;
    const double q = 1.0 + context.values[0] / 100.0 * alpha;
    const float next_fov = q == 1.0 ? fov : apex_ads::zoom_fov(fov, static_cast<float>(1.0 / q));
    Result result{};
    const Vec3 historical{stats.after[0], stats.after[1], stats.after[2]};
    if (!std::isfinite(next_fov) || next_fov <= 0 || next_fov >= 180
        || !finite(historical) || !finite(rotation)) return Status::reference_unavailable;
    const bool positioned = correct(historical, anchor, rotation,
                                    context.values[1] / 100.0, context.values[2] / 100.0, result);
    // Projection geometry does not control FOV; unchanged valid position remains safe.
    if ((!positioned && q == 1.0) || !state.framing_allowed(context, manager))
        return Status::reference_unavailable;
    Vec3 confirmation{};
    if (!body(context, confirmation) || std::memcmp(&anchor, &confirmation, sizeof(anchor)))
        return Status::body_unavailable;
    // The owning view callback validates the complete writable buffer first.
    // Validate the full position before commit; preview keeps the collision recovery ray alive.
    if (!apex_camera::memory_access(view, apex_view::view_required_size, true))
        return Status::reference_unavailable;
    if (write) {
        std::memcpy(static_cast<unsigned char*>(view) + apex_ads::FOV_OFFSET, &next_fov, sizeof(next_fov));
        if (positioned) std::memcpy(static_cast<unsigned char*>(view) + apex_view::view_location_offset,
                                    &result.location, sizeof(result.location));
    }
    if (positioned) std::memcpy(stats.after, &result.location, sizeof(result.location));
    if (zoom_pending) *zoom_pending = q > 1.0;
    return !positioned ? Status::position_unavailable
                       : unavailable ? Status::progress_unavailable : Status::applied;
}
}

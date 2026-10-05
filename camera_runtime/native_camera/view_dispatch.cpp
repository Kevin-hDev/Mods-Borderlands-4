#include "view_state.h"
#include "camera_memory.h"
#include "ads_api.h"
#include "ads_view.h"
#include <cmath>
#include <cstring>

namespace {
thread_local bool resolving = false;

bool resolve(apex_view::CollisionResolver callback, const apex_ads::CollisionQuery& query, double* output) {
    if (!callback || !std::isfinite(query.delta) || query.delta < 0) return false;
    bool accepted = false;
    resolving = true;
    __try {
        accepted = callback(&query, output) == 0;
    } __except(EXCEPTION_EXECUTE_HANDLER) { accepted = false; }
    resolving = false;
    for (size_t i = 0; i < 3; ++i) {
        if (!std::isfinite(output[i]) || std::abs(output[i]) > apex_view::max_coordinate) return false;
    }
    return accepted;
}
}

namespace apex_view::detail {
void dispatch(void* manager, void* view_target, float delta_time) {
    AcquireSRWLockExclusive(&guard);
    const bool expired = installed && deadline && GetTickCount64() >= deadline;
    if (expired) stop_locked();
    const bool owned = stats.active && manager == target_manager && !resolving
        && GetCurrentThreadId() == owner_thread;
    const auto entered_generation = generation;
    ReleaseSRWLockExclusive(&guard);
    auto& ads = apex_ads::shared_ads();
    if (expired) {
        const auto ads_generation = ads.statistics().generation;
        if (ads_generation) ads.clear(ads_generation);
    }
    bool effective = false;
    if (owned) effective = apex_ads::update_view(ads, manager, view_target, delta_time, original);
    else original(manager, view_target, delta_time);
    if (!owned) return;
    const auto ads_stats = ads.statistics();
    CollisionResolver callback = nullptr;
    apex_ads::CollisionQuery query{};
    auto candidate_framing_status = apex_framing::Status::disabled;
    bool extra_zoom_applied = false;
    AcquireSRWLockExclusive(&guard);
    __try {
        if (stats.active && manager == target_manager && generation == entered_generation) {
            framing_status = apex_framing::Status::disabled;
            framing_zoom_pending = false;
            stats.ads_effective = effective ? 1U : 0U;
            stats.ads_error = ads_stats.error;
            stats.ads_generation = ads_stats.generation;
            ++stats.calls;
            if (apex_camera::memory_access(view_target, view_required_size, true)
                && shift_view(config, view_target, stats, false)) {
                // Never expose an untested location, even to reentrant SDK calls.
                alignas(16) unsigned char preview[view_required_size]{};
                std::memcpy(preview, view_target, sizeof(preview));
                framing_zoom_pending = false;
                candidate_framing_status = framing.size
                    ? apex_framing::apply(ads, framing, manager, preview, stats, effective, !suspended,
                                          &apex_framing::native_progress, &framing_zoom_pending)
                    : apex_framing::Status::disabled;
                extra_zoom_applied = !suspended && framing_zoom_pending;
                // Obstruction affects only position. Native ADS and extra FOV stay independent.
                std::memcpy(static_cast<unsigned char*>(view_target) + apex_ads::FOV_OFFSET,
                            preview + apex_ads::FOV_OFFSET, sizeof(float));
                if (!suspended) {
                    query.manager = reinterpret_cast<uintptr_t>(manager);
                    std::memcpy(query.before, stats.before, sizeof(query.before));
                    std::memcpy(query.desired, stats.after, sizeof(query.desired));
                    query.delta = delta_time;
                    query.generation = generation;
                    callback = collision;
                }
                std::memcpy(stats.after, stats.before, sizeof(stats.after));
            } else ++stats.rejected;
        }
    } __finally {
        // Native progress exceptions keep their handler without retaining the bridge lock.
        if (AbnormalTermination()) {
            std::memcpy(stats.after, stats.before, sizeof(stats.after));
            framing_status = apex_framing::Status::reference_unavailable;
            framing_zoom_pending = false;
        }
        ReleaseSRWLockExclusive(&guard);
    }
    if (!query.manager) return;
    double output[3]{};
    // Physics may execute hooks: holding guard here would deadlock stats/stop/reentry.
    const bool accepted = resolve(callback, query, output);
    AcquireSRWLockExclusive(&guard);
    if (stats.active && !suspended && manager == target_manager
        && generation == query.generation
        && apex_camera::memory_access(view_target, view_required_size, true)) {
        if (accepted) {
            std::memcpy(static_cast<unsigned char*>(view_target) + view_location_offset,
                        output, sizeof(output));
            std::memcpy(stats.after, output, sizeof(stats.after));
            ++stats.writes;
            framing_status = candidate_framing_status;
        } else {
            ++stats.rejected;
            // Preview position was refused; only already committed extra FOV may be acknowledged.
            framing_status = candidate_framing_status == apex_framing::Status::disabled
                ? apex_framing::Status::disabled
                : extra_zoom_applied ? apex_framing::Status::position_unavailable
                                     : apex_framing::Status::reference_unavailable;
        }
    }
    ReleaseSRWLockExclusive(&guard);
}
}

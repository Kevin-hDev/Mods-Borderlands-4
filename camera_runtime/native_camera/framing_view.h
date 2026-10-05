#pragma once
#include "ads_state.h"
#include "view_target_bridge.h"

namespace apex_framing {
enum class Status : uint32_t {
    disabled = 0, applied = apex_ads::FRAMING_APPLIED,
    context_unavailable = apex_ads::FRAMING_CONTEXT_UNAVAILABLE,
    body_unavailable = apex_ads::FRAMING_BODY_UNAVAILABLE,
    progress_unavailable = apex_ads::FRAMING_POSITION_APPLIED_ZOOM_UNAVAILABLE,
    reference_unavailable = apex_ads::FRAMING_REFERENCE_UNAVAILABLE,
    position_unavailable = apex_ads::FRAMING_ZOOM_APPLIED_POSITION_UNAVAILABLE
};
using ProgressReader = bool (*)(void* manager, void* actor, float& output);
bool valid(const apex_ads::FramingContext& context);
bool native_progress(void* manager, void* actor, float& output);
Status apply(apex_ads::State& state, const apex_ads::FramingContext& context,
             void* manager, void* view, apex_view::Stats& stats,
             bool aiming, bool write, ProgressReader progress = &native_progress,
             bool* zoom_pending = nullptr);
}

#pragma once
#include "ads_state.h"

namespace apex_ads {
using Update = void (*)(void*, void*, float);
// The game's aim progress, 0 at the hip to 1 settled (framing_progress.cpp, apex_framing::native_progress).
using AimProgress = bool (*)(void* manager, void* actor, float& output);
float zoom_fov(float base, float scale);
float optic_scale(float optic, bool known, float progress);
bool update_view(State& state, void* manager, void* view, float delta, Update original,
                 AimProgress progress = nullptr);
}

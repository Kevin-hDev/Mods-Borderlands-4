#pragma once
#include "ads_state.h"

namespace apex_ads {
using Update = void (*)(void*, void*, float);
float zoom_fov(float base, float scale);
bool update_view(State& state, void* manager, void* view, float delta, Update original);
}

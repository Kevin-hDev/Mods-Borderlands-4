#pragma once
#include "interaction_bridge.h"
#include "view_target_bridge.h"

namespace apex_interaction {
constexpr uintptr_t pawn_offset = 0x3D0;
constexpr uintptr_t manager_offset = 0x448;
constexpr uintptr_t cache_time_offset = 0x1900;
constexpr uintptr_t cache_view_offset = 0x1910;
constexpr double max_camera_distance = 2000.0;
constexpr double radians_per_degree = 0.017453292519943295;
using ViewStats = int (*)(apex_view::Stats*);

// The game's eyes moved onto the camera's line at their own depth, looking where the camera looks; false when the
// view cannot be trusted, and then nothing is to be written.
bool align(const View& eyes, const View& camera, View& aligned);
// 1 = ready, 0 = mode/player no longer eligible, -1 = invalid camera data.
int read_camera(const Config& config, ViewStats getter, View& view);
ViewStats validate_camera(const Config& config, uintptr_t module);
}

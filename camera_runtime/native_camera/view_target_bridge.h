#pragma once

#include <cstddef>
#include <cstdint>
#include "generated_limits.h"
#include "generated_ads.h"

namespace apex_view {
constexpr std::uint32_t VIEW_TARGET_ABI = static_cast<uint32_t>(apex_ads::VIEW_ABI);
constexpr uint32_t update_slot = static_cast<uint32_t>(apex_ads::VIEW_UPDATE_SLOT);
constexpr uint32_t max_duration_ms = 60000;
constexpr uint64_t max_expected_rva = 0x80000000ULL;
constexpr size_t view_location_offset = 0x10;
constexpr size_t view_yaw_offset = 0x30;
constexpr size_t view_rotation_offset = 0x28;
constexpr size_t view_required_size = apex_ads::FOV_OFFSET + sizeof(float);
constexpr double max_offset = apex_limits::shoulder_max_offset;
constexpr double max_coordinate = static_cast<double>(apex_ads::CAMERA_MAX_COORDINATE);
constexpr double max_yaw = 360000.0;
constexpr double degrees_to_radians = 0.017453292519943295;

using Config = apex_ads::ViewConfig;
using Stats = apex_ads::ViewStats;
using CollisionResolver = int (*)(const apex_ads::CollisionQuery*, double*);

bool valid_config(const Config& config);
bool shift_view(const Config& config, void* view_target, Stats& stats, bool write);
}

#define VIEW_API extern "C" __declspec(dllexport)
VIEW_API int view_start(void* manager, const apex_view::Config* config);
VIEW_API int view_stop();
VIEW_API int view_set_collision(apex_view::CollisionResolver resolver);
VIEW_API int view_set_suspended(uint32_t suspended);
VIEW_API bool view_set_right(double right);
VIEW_API int view_set_transition_duration(double seconds);
VIEW_API int view_set_climb_suspended(uint32_t suspended);
VIEW_API int view_set_offset_suspended(uint32_t suspended, double seconds);
VIEW_API bool view_offset_transition_active();
VIEW_API int view_stats(apex_view::Stats* output);
VIEW_API int view_set_framing(const apex_ads::FramingContext* context);
VIEW_API uint32_t view_framing_status();
VIEW_API bool view_framing_zoom_pending();

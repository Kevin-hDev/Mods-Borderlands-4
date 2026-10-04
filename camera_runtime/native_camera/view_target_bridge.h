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
constexpr size_t view_required_size = view_yaw_offset + sizeof(double);
constexpr double max_offset = apex_limits::shoulder_max_offset;
constexpr double max_coordinate = 1.0e9;
constexpr double max_yaw = 360000.0;
constexpr double degrees_to_radians = 0.017453292519943295;

using Config = apex_ads::ViewConfig;
using Stats = apex_ads::ViewStats;

bool valid_config(const Config& config);
bool shift_view(const Config& config, void* view_target, Stats& stats, bool write);
}

#define VIEW_API extern "C" __declspec(dllexport)
VIEW_API int view_start(void* manager, const apex_view::Config* config);
VIEW_API int view_stop();
VIEW_API int view_set_suspended(uint32_t suspended);
VIEW_API bool view_set_right(double right);
VIEW_API int view_stats(apex_view::Stats* output);

#pragma once

#include <cstddef>
#include <cstdint>

namespace apex_view {
constexpr uint32_t abi_version = 4;
constexpr uint32_t update_slot = 264;
constexpr uint32_t max_duration_ms = 60000;
constexpr uint64_t max_expected_rva = 0x80000000ULL;
constexpr size_t view_location_offset = 0x10;
constexpr size_t view_yaw_offset = 0x30;
constexpr size_t view_required_size = view_yaw_offset + sizeof(double);
constexpr double max_offset = 150.0;
constexpr double max_coordinate = 1.0e9;
constexpr double max_yaw = 360000.0;
constexpr double degrees_to_radians = 0.017453292519943295;

struct Config {
    uint32_t abi, duration_ms, slot_index, reserved;
    uint64_t expected_rva;
    double right, up;
};

struct Stats {
    uint64_t calls, writes, rejected;
    double before[3], after[3], yaw;
    uint32_t active, slot_index, suspended, reserved;
};

static_assert(sizeof(Config) == 40 && sizeof(Stats) == 96, "Unexpected view bridge ABI");

bool valid_config(const Config& config);
bool shift_view(const Config& config, void* view_target, Stats& stats, bool write);
}

#define VIEW_API extern "C" __declspec(dllexport)
VIEW_API int view_start(void* manager, const apex_view::Config* config);
VIEW_API int view_stop();
VIEW_API int view_set_suspended(uint32_t suspended);
VIEW_API int view_stats(apex_view::Stats* output);

#pragma once
#include <cstddef>
#include <cstdint>
#include "generated_ads.h"

namespace apex_interaction {
constexpr uint32_t abi = static_cast<uint32_t>(apex_ads::INTERACTION_ABI);
constexpr uintptr_t provider_offset = 0xDA8;
constexpr uintptr_t provider_rva = 0x1E4996;
constexpr uintptr_t table_rva = 0xB98B8F0;
constexpr size_t provider_slot = 0x40 / sizeof(void*);
constexpr double max_coordinate = 100000000.0;
constexpr double max_angle = 100000.0;
using Provider = bool (*)(void*, void*);

struct Config {
    uint32_t abi, reserved;
    uint64_t controller, pawn, manager, camera_module;
};
struct Sample { double origin[3], rotation[3], anchor[3]; };
struct Stats {
    uint64_t calls, matches, valid, invalid, tick_ms;
    Sample sample;
    uint32_t active, installed, last_success, reserved;
    uint64_t writes, bypassed, rejected_view;
    double output_origin[3], output_rotation[3];
};
static_assert(sizeof(Config) == 40);
static_assert(sizeof(Sample) == 72);
static_assert(sizeof(Stats) == 200);

bool passive_call(Provider original, void* self, void* output, void* target,
                  Sample& sample, bool& valid);
}

extern "C" {
__declspec(dllexport) int interaction_start(const apex_interaction::Config* config);
__declspec(dllexport) int interaction_stop();
__declspec(dllexport) int interaction_stats(apex_interaction::Stats* output);
}

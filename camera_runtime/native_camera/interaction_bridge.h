#pragma once
#include <cstddef>
#include <cstdint>
#include "generated_ads.h"

// The hunter's eyes on the crosshair's line in third person (docs/third_person_fov/camera/
// 2026-10-08-plan-yeux-sur-la-camera.md): the game aims throws and pickups from OakCharacter's eyes view point,
// which is the camera only in first person.
namespace apex_interaction {
constexpr uint32_t abi = static_cast<uint32_t>(apex_ads::INTERACTION_ABI);
// OakCharacter's eyes view point, slot +0x588 of its table: void(this, FVector* location, FRotator* rotation).
constexpr uintptr_t eyes_rva = 0x4904496;
constexpr uintptr_t cache_read_rva = 0x48814D9;
constexpr size_t eyes_slot = 0x588 / sizeof(void*);
constexpr double max_coordinate = 100000000.0;
constexpr double max_angle = 100000.0;
using Eyes = void (*)(void*, void*, void*);

struct Config {
    uint32_t abi, reserved;
    uint64_t controller, pawn, manager, camera_module;
};
// A place and a rotation (pitch, yaw, roll), as the engine's FVector and FRotator hold them.
struct View { double origin[3], rotation[3]; };
struct Stats {
    // calls: the hunter's eyes asked while installed; valid: answers the game gave in range.
    uint64_t calls, valid, invalid, tick_ms;
    uint32_t active, installed;
    uint64_t writes, bypassed, rejected_view;
    View eyes, output;
};
static_assert(sizeof(Config) == 40);
static_assert(sizeof(View) == 48);
static_assert(sizeof(Stats) == 160);

// Ask the game's eyes; true with its answer in `before` when they are the target's and in range.
bool passive_call(Eyes original, void* self, void* location, void* rotation, void* target, View& before);
}

extern "C" {
__declspec(dllexport) int interaction_start(const apex_interaction::Config* config);
__declspec(dllexport) int interaction_stop();
__declspec(dllexport) int interaction_stats(apex_interaction::Stats* output);
}

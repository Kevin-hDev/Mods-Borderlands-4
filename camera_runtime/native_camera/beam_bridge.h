#pragma once
#include <cstddef>
#include <cstdint>
#include "interaction_bridge.h"

// The hunter's beams on the crosshair's line in third person (docs/investigations/third_person_fov/camera/
// 2026-10-21-rayon-ohm-et-couteau.md). In third person the game starts a LightBeam's query (Ohm I Got) from the
// hunter's own view point, parallel to the view, so it lands beside the crosshair on the hunter's side; the eyes the
// interaction alignment corrects are not asked (measured on 2026-10-21).
namespace apex_beam {
// LightBeam fields, read in the Steam executable 9c3afb7d and in game on 2026-10-21: the query's origin and unit
// direction, FVectors of doubles, set before the endpoint step and read by it.
constexpr uintptr_t origin_offset = 0x388;
constexpr uintptr_t direction_offset = 0x3A0;
// The endpoint step, slot +0x368 of OakLightBeam's table: void(this, float delta). It ends the query at origin +
// direction x length; the beam's collision is checked along that line afterwards.
constexpr size_t endpoint_slot = 0x368 / sizeof(void*);
constexpr uint32_t max_field_offset = 0x1000;
// A query aimed more than 10 degrees away from the view is not aimed by the crosshair (a beam locked elsewhere): left
// as the game made it. The dynamic camera turns the view about 2 degrees from the controller (2026-10-08).
constexpr double min_view_cosine = 0.98480775301220806;
using Endpoint = void (*)(void*, float);

struct Config {
    apex_interaction::Config camera;
    // OakLightBeam's class default object: its table is every OakLightBeam's, beams of Blueprint classes included.
    uint64_t beam_default;
    // Where a beam holds its instigator (ClientState.instigator), from the SDK's own types.
    uint32_t instigator_offset, reserved;
};
// A beam query: where it starts and the unit vector it runs along.
struct Query { double origin[3], direction[3]; };
struct Stats {
    // calls: the hunter's beams ended while installed; writes: those moved onto the crosshair's line;
    // off_view: queries aimed away from the view, left alone.
    uint64_t calls, writes, bypassed, rejected_view, off_view, tick_ms;
    uint32_t active, installed;
    Query before, after;
};
static_assert(sizeof(Config) == 56);
static_assert(sizeof(Query) == 48);
static_assert(sizeof(Stats) == 152);

enum class Alignment { written, rejected_view, off_view };
// The query moved onto the camera's line at its own depth, along the camera's forward. Anything but `written`
// leaves `aligned` untouched and nothing is to be written.
Alignment align_query(const Query& game, const apex_interaction::View& camera, Query& aligned);
}

extern "C" {
__declspec(dllexport) int beam_start(const apex_beam::Config* config);
__declspec(dllexport) int beam_stop();
__declspec(dllexport) int beam_stats(apex_beam::Stats* output);
}

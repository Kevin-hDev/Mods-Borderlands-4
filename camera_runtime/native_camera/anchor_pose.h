#pragma once
#include <cstddef>
#include <cstdint>

namespace climb_anchor {
using Update = void (*)(void*, void*, void*, float);
constexpr size_t state_bytes = 0x70;
constexpr size_t position_offset = 0x30;
constexpr size_t behavior_bytes = 0x30;
constexpr size_t flags_offset = 0x18;
constexpr size_t behavior_socket_offset = 0x1C;
constexpr double max_adjustment = 1000.0;
// Keep this anchor upstream of native RelativeOffset and CollisionOffsetTrace.
bool apply_socket(Update socket, void* context, void* state, float delta, uint64_t socket_name);
}

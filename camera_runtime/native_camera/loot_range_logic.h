#pragma once
#include <cstddef>
#include <cstdint>
#include "generated_limits.h"

namespace apex_loot {
constexpr float min_distance = static_cast<float>(apex_limits::loot_base_distance);
constexpr float max_distance = static_cast<float>(apex_limits::loot_max_distance);
constexpr size_t config_size = 0x108;
constexpr size_t custom_flag_offset = 0x1B;
constexpr size_t custom_distance_offset = 0x1C;
constexpr size_t pool_size = 8;
constexpr uintptr_t pickup_slot_rva = 0xB310750;
constexpr uintptr_t pickup_getter_rva = 0x3C53BF2;
constexpr uintptr_t pickup_primary_caller_rva = 0x3E559F7;
constexpr uintptr_t pickup_secondary_caller_rva = 0x3E55EAF;
constexpr uintptr_t lootable_caller_rva = 0x3E54834;
struct alignas(8) ConfigImage { unsigned char bytes[config_size]; };
struct OverridePool { ConfigImage slots[pool_size]{}; uint32_t cursor = 0; };
bool valid_distance(float distance);
const void* prepare_override(uintptr_t caller, const void* original, float distance, OverridePool& pool);
}

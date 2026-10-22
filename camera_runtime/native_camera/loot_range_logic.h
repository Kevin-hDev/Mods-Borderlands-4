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
// Where the loot path sits in one game build: InventoryPickup's usability table slot and its getter, the getter's two
// pickup consumers, the container consumer and UsabilityConfigInfo's 0x108-byte size.
struct Addresses {
    uintptr_t pickup_slot, pickup_getter, pickup_primary_caller, pickup_secondary_caller, lootable_caller, struct_size;
};
// One row per build whose loot path was measured (releves/third_person_fov/2026-09-25-loot-range,
// releves/third_person_fov/2026-10-22-mise-a-jour-jeu). The game carries no build number here, so the row whose every
// fingerprint matches is used (loot_range_fingerprints.cpp); none matching means no loot range, as before.
constexpr Addresses builds[] = {
    {0xB310750, 0x3C53BF2, 0x3E559F7, 0x3E55EAF, 0x3E54834, 0x6538897}, // Steam 4845623
    {0xB318290, 0x3C55BBA, 0x3E5A3CF, 0x3E5A887, 0x3E5920C, 0x65413E3}, // Steam 4906557, 2026-10-22
};
struct alignas(8) ConfigImage { unsigned char bytes[config_size]; };
struct OverridePool { ConfigImage slots[pool_size]{}; uint32_t cursor = 0; };
bool valid_distance(float distance);
const void* prepare_override(const Addresses& build, uintptr_t caller, const void* original, float distance,
                             OverridePool& pool);
}

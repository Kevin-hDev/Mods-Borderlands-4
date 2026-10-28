#pragma once

#include "loot_range_logic.h"
#include <cstdint>

namespace apex_loot {
// The build row whose callers, size and pickup table all match this game, or nullptr.
const Addresses* matching_build(uintptr_t module);
}

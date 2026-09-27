#include "loot_range_logic.h"
#include <cassert>
#include <cmath>
#include <cstring>
#include <iostream>

int main() {
    using namespace apex_loot;
    assert(valid_distance(660.0F));
    assert(!valid_distance(NAN));
    assert(!valid_distance(329.0F));
    assert(!valid_distance(991.0F));
    OverridePool pool{};
    int marker = 7;
    assert(prepare_override(0, &marker, 660, pool) == &marker);
    const auto* out = static_cast<const unsigned char*>(
        prepare_override(pickup_primary_caller_rva, &marker, 660, pool));
    assert(out != reinterpret_cast<void*>(&marker));
    assert(out[custom_flag_offset] == 1);
    float distance{};
    std::memcpy(&distance, out + custom_distance_offset, sizeof(distance));
    assert(distance == 660);
    for (size_t i = 0; i < config_size; ++i) {
        if (i < custom_flag_offset || i >= custom_distance_offset + 4) assert(out[i] == 0);
    }
    // Only the two pickup selection consumers receive a copied config, never vendors or NPCs.
    assert(prepare_override(0x3E54834, &marker, 660, pool) == &marker);
    assert(prepare_override(pickup_secondary_caller_rva, nullptr, 990, pool));
    std::cout << "RESULTAT: OK - pickup range copies and exclusions\n";
}

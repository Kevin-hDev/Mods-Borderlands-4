#include <cstddef>
#include "interaction_bridge.h"
#include <cassert>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>

namespace {
unsigned calls = 0;
apex_interaction::View source{{100, 200, 300}, {1, 2, 3}};
void original(void*, void* location, void* rotation) {
    ++calls;
    if (location) std::memcpy(location, source.origin, sizeof(source.origin));
    if (rotation) std::memcpy(rotation, source.rotation, sizeof(source.rotation));
}
}

int main() {
    int hunter{}, enemy{};
    double location[3]{}, rotation[3]{};
    apex_interaction::View before{};
    assert(apex_interaction::passive_call(original, &hunter, location, rotation, &hunter, before));
    assert(calls == 1 && std::memcmp(location, source.origin, sizeof(location)) == 0
           && std::memcmp(rotation, source.rotation, sizeof(rotation)) == 0);
    assert(std::memcmp(&before, &source, sizeof(source)) == 0);
    // Another character's eyes are the game's, and never read as the hunter's.
    assert(!apex_interaction::passive_call(original, &enemy, location, rotation, &hunter, before));
    assert(calls == 2);
    assert(!apex_interaction::passive_call(original, &hunter, nullptr, rotation, &hunter, before));
    assert(calls == 3);
    source.rotation[1] = std::numeric_limits<double>::quiet_NaN();
    assert(!apex_interaction::passive_call(original, &hunter, location, rotation, &hunter, before));
    assert(calls == 4 && std::isnan(rotation[1]));
    source.rotation[1] = 2;
    source.origin[0] = apex_interaction::max_coordinate * 2;
    assert(!apex_interaction::passive_call(original, &hunter, location, rotation, &hunter, before));
    assert(calls == 5);
    apex_interaction::Config config{apex_interaction::abi, 0, 0, 0, 0, 0};
    assert(interaction_start(&config) == 1);
    // An address nothing occupies in this process: the pawn cannot be read.
    config.pawn = 0x100000000000;
    assert(interaction_start(&config) == 1);
    config.controller = 0x30000;
    config.abi += 1;
    assert(interaction_start(&config) == 1);
    config.abi -= 1;
    assert(interaction_start(&config) == 2);
    assert(interaction_start(nullptr) == 1);
    assert(interaction_stop() == 0);
    apex_interaction::Stats stats{};
    assert(interaction_stats(&stats) == 0 && !stats.active && !stats.installed && !stats.calls);
    assert(interaction_stats(nullptr) == 1);
    std::cout << "RESULTAT: OK - the game's eyes answer first, only the hunter's are read\n";
}

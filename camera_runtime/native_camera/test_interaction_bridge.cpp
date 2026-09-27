#include <cstddef>
#include "interaction_bridge.h"
#include <cassert>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>

namespace {
unsigned calls = 0;
bool response = true;
apex_interaction::Sample source{{100, 200, 300}, {1, 2, 3}, {4, 5, 6}};
bool original(void*, void* output) {
    ++calls;
    if (output) std::memcpy(output, &source, sizeof(source));
    return response;
}
}

int main() {
    int owner{}, other{};
    apex_interaction::Sample output{}, sampled{};
    bool valid = false;
    assert(apex_interaction::passive_call(original, &owner, &output, &owner, sampled, valid));
    assert(valid && calls == 1 && std::memcmp(&output, &source, sizeof(source)) == 0);
    assert(std::memcmp(&sampled, &source, sizeof(source)) == 0);
    assert(apex_interaction::passive_call(original, &other, &output, &owner, sampled, valid));
    assert(!valid && calls == 2);
    response = false;
    assert(!apex_interaction::passive_call(original, &owner, &output, &owner, sampled, valid));
    assert(!valid && calls == 3);
    response = true;
    assert(apex_interaction::passive_call(original, &owner, nullptr, &owner, sampled, valid));
    assert(!valid && calls == 4);
    source.rotation[1] = std::numeric_limits<double>::quiet_NaN();
    assert(apex_interaction::passive_call(original, &owner, &output, &owner, sampled, valid));
    assert(!valid && calls == 5 && std::isnan(output.rotation[1]));
    apex_interaction::Config config{apex_interaction::abi, 0, 0, 0, 0, 0};
    assert(interaction_start(&config) != 0);
    assert(interaction_stop() == 0);
    apex_interaction::Stats stats{};
    assert(interaction_stats(&stats) == 0 && !stats.active && !stats.installed);
    std::cout << "RESULTAT: OK - passive callback preserves original result and output\n";
}

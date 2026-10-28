#include "ads_mode.h"
#include <cassert>
#include <cstring>
#include <iostream>
#include <limits>
#include "ads_test_assert.h"

using namespace apex_ads;
alignas(16) unsigned char manager[0x3b00]{}, mode[0xb00]{};
template<class T> void put(unsigned char* target, size_t offset, T value) {
    std::memcpy(target + offset, &value, sizeof(value));
}

int main() {
    constexpr uint64_t third = 0x1234;
    put(manager, MANAGER_MODE_OFFSET, third);
    put(manager, MANAGER_MODE_OBJECT_OFFSET, reinterpret_cast<uintptr_t>(mode));
    ModeSnapshot result{};
    assert(read_mode(manager, third, result) && result.stable && result.name == third);
    for (float remaining : {0.001f, -1.0f, std::numeric_limits<float>::infinity(),
                            std::numeric_limits<float>::quiet_NaN()}) {
        put(mode, MODE_BLEND_REMAINING_OFFSET, remaining);
        assert(!read_mode(manager, third, result));
    }
    put(mode, MODE_BLEND_REMAINING_OFFSET, 0.0f);
    put(mode, MODE_TRANSITION_FLAG_OFFSET, uint8_t{1});
    assert(!read_mode(manager, third, result));
    put(mode, MODE_TRANSITION_FLAG_OFFSET, uint8_t{0});
    for (uint64_t foreign : {uint64_t{0}, uint64_t{10}, uint64_t{11}, uint64_t{12}}) {
        put(manager, MANAGER_MODE_OFFSET, foreign);
        assert(!read_mode(manager, third, result));
    }
    put(manager, MANAGER_MODE_OFFSET, third);
    put(manager, MANAGER_MODE_OBJECT_OFFSET, uintptr_t{1});
    assert(!read_mode(manager, third, result));
    assert(!read_mode(nullptr, third, result));
    assert(!read_mode(manager, 0, result));
    std::cout << "RESULTAT: OK (fresh native mode and transition)\n";
}

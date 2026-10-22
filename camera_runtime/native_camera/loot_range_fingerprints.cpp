#include "loot_range_fingerprints.h"
#include "camera_memory.h"

#include <cstring>

namespace apex_loot {
namespace {
bool bytes_equal(uintptr_t address, const unsigned char* expected, size_t length) {
    void* raw = reinterpret_cast<void*>(address);
    return apex_camera::memory_access(raw, length)
        && std::memcmp(raw, expected, length) == 0;
}

bool fingerprints_match(uintptr_t module, const Addresses& build) {
    static constexpr unsigned char first_call[] = {0xFF, 0x50, 0x10, 0x41, 0xF6, 0x85};
    static constexpr unsigned char pickup_call[] = {0xFF, 0x50, 0x10, 0x48, 0x8B, 0x4C};
    static constexpr unsigned char struct_size[] = {0x48, 0xB9, 0x08, 0x01, 0x00,
                                                     0x00, 0x08, 0x00, 0x00, 0x00};
    auto* expected = reinterpret_cast<void*>(module + build.pickup_getter);
    auto** slot = reinterpret_cast<void**>(module + build.pickup_slot);
    return bytes_equal(module + build.lootable_caller - 3, first_call, sizeof(first_call))
        && bytes_equal(module + build.pickup_primary_caller - 3, pickup_call, sizeof(pickup_call))
        && bytes_equal(module + build.pickup_secondary_caller - 3, pickup_call, sizeof(pickup_call))
        && bytes_equal(module + build.struct_size, struct_size, sizeof(struct_size))
        && apex_camera::memory_access(slot, sizeof(void*)) && *slot == expected
        && apex_camera::executable_in_main_module(expected);
}
}

const Addresses* matching_build(uintptr_t module) {
    for (const auto& build : builds) {
        if (fingerprints_match(module, build)) return &build;
    }
    return nullptr;
}
}

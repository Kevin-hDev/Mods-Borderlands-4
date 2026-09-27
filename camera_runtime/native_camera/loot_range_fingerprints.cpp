#include "loot_range_fingerprints.h"
#include "loot_range_logic.h"
#include "camera_memory.h"

#include <cstring>

namespace apex_loot {
namespace {
constexpr uintptr_t struct_size_rva = 0x6538897;

bool bytes_equal(uintptr_t address, const unsigned char* expected, size_t length) {
    void* raw = reinterpret_cast<void*>(address);
    return apex_camera::memory_access(raw, length)
        && std::memcmp(raw, expected, length) == 0;
}
}

bool range_fingerprints_match(uintptr_t module) {
    static constexpr unsigned char first_call[] = {0xFF, 0x50, 0x10, 0x41, 0xF6, 0x85};
    static constexpr unsigned char pickup_call[] = {0xFF, 0x50, 0x10, 0x48, 0x8B, 0x4C};
    static constexpr unsigned char struct_size[] = {0x48, 0xB9, 0x08, 0x01, 0x00,
                                                     0x00, 0x08, 0x00, 0x00, 0x00};
    return bytes_equal(module + lootable_caller_rva - 3, first_call, sizeof(first_call))
        && bytes_equal(module + pickup_primary_caller_rva - 3, pickup_call, sizeof(pickup_call))
        && bytes_equal(module + pickup_secondary_caller_rva - 3, pickup_call, sizeof(pickup_call))
        && bytes_equal(module + struct_size_rva, struct_size, sizeof(struct_size));
}
}

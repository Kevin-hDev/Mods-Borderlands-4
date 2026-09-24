#include "view_target_bridge.h"

#include <windows.h>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iostream>

#undef assert
#define assert(condition) do { if (!(condition)) { \
    std::cerr << "RESULTAT: ECHEC line=" << __LINE__ << "\n"; std::exit(1); \
} } while (false)

using namespace apex_view;
using Update = void (*)(void*, void*, float);

struct Manager { void** table; };
struct ViewTarget { alignas(16) unsigned char bytes[64]{}; };

double read_value(const ViewTarget& view, size_t offset) {
    double value;
    std::memcpy(&value, view.bytes + offset, sizeof(value));
    return value;
}

void write_value(ViewTarget& view, size_t offset, double value) {
    std::memcpy(view.bytes + offset, &value, sizeof(value));
}

__declspec(noinline) void original_update(void*, void* raw_view, float) {
    if (raw_view) {
        auto& view = *static_cast<ViewTarget*>(raw_view);
        write_value(view, view_location_offset, read_value(view, view_location_offset) + 5.0);
    }
}

void invoke(Manager& manager, ViewTarget& view) {
    reinterpret_cast<Update>(manager.table[update_slot])(&manager, &view, 0.016f);
}

bool close_to(double value, double expected) { return std::abs(value - expected) < 1e-9; }

Config make_config(uint32_t duration_ms = 0) {
    const auto module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const auto function = reinterpret_cast<uintptr_t>(&original_update);
    return Config{abi_version, duration_ms, update_slot, 0,
                  static_cast<uint64_t>(function - module), 35.0, 5.0};
}

int main() {
    auto* table = static_cast<void**>(VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
    assert(table);
    table[update_slot] = reinterpret_cast<void*>(&original_update);
    DWORD previous;
    assert(VirtualProtect(table, 4096, PAGE_READONLY, &previous));
    Manager manager{table};
    auto config = make_config();
    assert(valid_config(config) && view_start(&manager, &config) == 0);

    ViewTarget shifted{};
    write_value(shifted, view_location_offset, 10.0);
    write_value(shifted, view_location_offset + 8, 20.0);
    write_value(shifted, view_location_offset + 16, 30.0);
    write_value(shifted, view_yaw_offset, 0.0);
    invoke(manager, shifted);
    assert(close_to(read_value(shifted, view_location_offset), 15.0));
    assert(close_to(read_value(shifted, view_location_offset + 8), 55.0));
    assert(close_to(read_value(shifted, view_location_offset + 16), 35.0));

    assert(view_set_suspended(1) == 0);
    ViewTarget guarded{};
    write_value(guarded, view_yaw_offset, 0.0);
    invoke(manager, guarded);
    assert(close_to(read_value(guarded, view_location_offset), 5.0));
    Stats stats{};
    assert(view_stats(&stats) == 0);
    assert(stats.active == 1 && stats.suspended == 1 && stats.writes == 1);
    assert(close_to(stats.before[0], 5.0) && close_to(stats.after[1], 35.0));

    assert(view_set_suspended(0) == 0);
    invoke(manager, guarded);
    assert(close_to(read_value(guarded, view_location_offset + 8), 35.0));
    assert(view_stop() == 0 && table[update_slot] == reinterpret_cast<void*>(&original_update));

    config = make_config(1);
    assert(view_start(&manager, &config) == 0);
    Sleep(10);
    ViewTarget expired{};
    invoke(manager, expired);
    assert(close_to(read_value(expired, view_location_offset), 5.0));
    assert(view_stop() == 0);
    assert(VirtualFree(table, 0, MEM_RELEASE));
    std::cout << "RESULTAT: OK - persistent bridge, suspension, expiry, restore\n";
}

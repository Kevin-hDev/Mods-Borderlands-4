#include "view_target_bridge.h"
#include "ads_api.h"
#include "ads_native_test_fixture.h"

#include <windows.h>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <thread>

#undef assert
#define assert(condition) do { if (!(condition)) { \
    std::cerr << "RESULTAT: ECHEC line=" << __LINE__ << "\n"; std::exit(1); \
} } while (false)

using namespace apex_view;
using Update = void (*)(void*, void*, float);

struct Manager { void** table; };
struct ViewTarget { alignas(16) unsigned char bytes[80]{}; };

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
        const float fov = 110.0f;
        std::memcpy(view.bytes + apex_ads::FOV_OFFSET, &fov, sizeof(fov));
    }
}

void invoke(Manager& manager, ViewTarget& view) {
    reinterpret_cast<Update>(manager.table[update_slot])(&manager, &view, 0.016f);
}

bool close_to(double value, double expected) { return std::abs(value - expected) < 1e-9; }

Config make_config(uint32_t duration_ms = 0) {
    const auto module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const auto function = reinterpret_cast<uintptr_t>(&original_update);
    return Config{VIEW_TARGET_ABI, duration_ms, update_slot, 0,
                  static_cast<uint64_t>(function - module), 35.0, 5.0};
}

int collision_calls = 0;
bool reject_collision = false;
bool stop_in_collision = false;
bool clip_collision = false;
int resolve_collision(const apex_ads::CollisionQuery* query, double* output) {
    ++collision_calls;
    Stats live{};
    assert(view_stats(&live) == 0); // The callback must run without the bridge lock held.
    if (stop_in_collision) assert(view_stop() == 0);
    if (reject_collision) return 1;
    std::memcpy(output, query->desired, sizeof(query->desired));
    if (clip_collision) output[1] = (query->before[1] + query->desired[1]) / 2;
    return 0;
}

int main() {
    auto* table = static_cast<void**>(VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
    assert(table);
    table[update_slot] = reinterpret_cast<void*>(&original_update);
    DWORD previous;
    assert(VirtualProtect(table, 4096, PAGE_READONLY, &previous));
    Manager manager{table};
    auto config = make_config();
    assert(!view_set_right(0.0));
    assert(valid_config(config) && view_start(&manager, &config) == 0);
    assert(view_set_collision(reinterpret_cast<CollisionResolver>(1)) != 0);
    assert(view_set_collision(&resolve_collision) == 0);

    ViewTarget shifted{};
    write_value(shifted, view_location_offset, 10.0);
    write_value(shifted, view_location_offset + 8, 20.0);
    write_value(shifted, view_location_offset + 16, 30.0);
    write_value(shifted, view_yaw_offset, 0.0);
    invoke(manager, shifted);
    assert(close_to(read_value(shifted, view_location_offset), 15.0));
    assert(close_to(read_value(shifted, view_location_offset + 8), 55.0));
    assert(close_to(read_value(shifted, view_location_offset + 16), 35.0));

    assert(view_set_right(-35.0));
    ViewTarget left{};
    write_value(left, view_yaw_offset, 0.0);
    invoke(manager, left);
    assert(close_to(read_value(left, view_location_offset + 8), -35.0));
    assert(view_set_right(150.0) && view_set_right(-150.0));
    assert(!view_set_right(std::numeric_limits<double>::quiet_NaN()));
    assert(!view_set_right(std::numeric_limits<double>::infinity()));
    assert(!view_set_right(150.001));
    ViewTarget kept{};
    write_value(kept, view_yaw_offset, 0.0);
    invoke(manager, kept);
    assert(close_to(read_value(kept, view_location_offset + 8), -150.0));

    assert(view_set_suspended(1) == 0);
    ViewTarget guarded{};
    write_value(guarded, view_yaw_offset, 0.0);
    invoke(manager, guarded);
    assert(close_to(read_value(guarded, view_location_offset), 5.0));
    Stats stats{};
    assert(view_stats(&stats) == 0);
    assert(stats.active == 1 && stats.suspended == 1 && stats.writes == 3);
    assert(close_to(stats.before[0], 5.0) && close_to(stats.after[1], 0.0));

    assert(view_set_suspended(0) == 0);
    invoke(manager, guarded);
    assert(close_to(read_value(guarded, view_location_offset + 8), -150.0));
    assert(view_stop() == 0 && table[update_slot] == reinterpret_cast<void*>(&original_update));

    config = make_config();
    assert(view_start(&manager, &config) == 0);
    assert(view_set_collision(&resolve_collision) == 0);
    reject_collision = true;
    ViewTarget collision_failed{};
    invoke(manager, collision_failed);
    assert(close_to(read_value(collision_failed, view_location_offset + 8), 0.0));
    assert(view_stats(&stats) == 0 && stats.rejected == 1 && stats.suspended == 0);
    reject_collision = false;
    clip_collision = true;
    invoke(manager, collision_failed);
    assert(close_to(read_value(collision_failed, view_location_offset + 8), 17.5));
    assert(view_stats(&stats) == 0 && close_to(stats.after[1], 17.5));
    clip_collision = false;
    write_value(collision_failed, view_location_offset + 8, 0.0);
    stop_in_collision = true;
    invoke(manager, collision_failed);
    assert(close_to(read_value(collision_failed, view_location_offset + 8), 0.0));
    stop_in_collision = false;
    assert(view_stop() == 0);

    assert(view_start(&manager, &config) == 0);
    assert(view_set_collision(&resolve_collision) == 0);
    const int previous_calls = collision_calls;
    int foreign_stop = 0;
    std::thread worker([&] {
        ViewTarget threaded{};
        invoke(manager, threaded);
        foreign_stop = view_stop();
        assert(close_to(read_value(threaded, view_location_offset + 8), 0.0));
    });
    worker.join();
    assert(collision_calls == previous_calls && foreign_stop != 0);
    assert(view_stop() == 0);

    config = make_config(1);
    assert(view_start(&manager, &config) == 0);
    Sleep(10);
    ViewTarget expired{};
    invoke(manager, expired);
    assert(close_to(read_value(expired, view_location_offset), 5.0));
    assert(view_stop() == 0);
    apex_ads::NativeFixture fixture;
    auto& ads = apex_ads::shared_ads();
    assert(ads.configure(fixture.table_address(), fixture.third, fixture.zoom));
    ads.set_installed(true);
    fixture.put(2, 0, reinterpret_cast<uintptr_t>(table));
    auto* ads_manager = static_cast<Manager*>(fixture.manager());
    config = make_config();
    assert(view_start(ads_manager, &config) == 0);
    assert(ads.publish(fixture.context(1)) == 0);
    assert(view_set_suspended(1) == 0);
    ViewTarget aimed{};
    invoke(*ads_manager, aimed);
    float fov{};
    std::memcpy(&fov, aimed.bytes + apex_ads::FOV_OFFSET, sizeof(fov));
    assert(std::abs(fov - 71.05929f) < 0.001f);
    assert(close_to(read_value(aimed, view_location_offset + 8), 0.0));
    assert(view_stats(&stats) == 0 && stats.ads_effective == 1 && stats.ads_generation == 1);
    assert(ads.statistics().fov_writes == 1);
    assert(view_set_suspended(0) == 0);
    assert(view_set_collision(&resolve_collision) == 0);
    reject_collision = true;
    ViewTarget obstructed_ads{};
    invoke(*ads_manager, obstructed_ads);
    std::memcpy(&fov, obstructed_ads.bytes + apex_ads::FOV_OFFSET, sizeof(fov));
    assert(std::abs(fov - 71.05929f) < 0.001f);
    assert(close_to(read_value(obstructed_ads, view_location_offset + 8), 0.0));
    assert(view_stats(&stats) == 0 && stats.suspended == 0 && stats.rejected == 1);
    reject_collision = false;
    ViewTarget foreign{};
    invoke(manager, foreign);
    assert(ads.statistics().fov_writes == 2);
    assert(view_stop() == 0 && ads.statistics().active == 0);
    assert(VirtualFree(table, 0, MEM_RELEASE));
    std::cout << "RESULTAT: OK - persistent bridge, suspension, expiry, restore\n";
}

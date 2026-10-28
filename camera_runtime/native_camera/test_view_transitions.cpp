#include "view_target_bridge.h"
#include <windows.h>
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <thread>

#define check(condition) do { if (!(condition)) { \
    std::cerr << "RESULTAT: ECHEC line=" << __LINE__ << '\n'; std::exit(1); \
} } while (false)

struct Manager { void** table; };
struct View { alignas(16) unsigned char data[80]{}; };
bool blocked = false;
int calls = 0;
double last_desired = 0;

__declspec(noinline) void native_update(void*, void* raw, float) {
    auto* view = static_cast<View*>(raw);
    const double xyz[3]{10, 20, 30}, yaw = 0;
    const float fov = 110;
    std::memcpy(view->data + apex_view::view_location_offset, xyz, sizeof(xyz));
    std::memcpy(view->data + apex_view::view_yaw_offset, &yaw, sizeof(yaw));
    std::memcpy(view->data + apex_ads::FOV_OFFSET, &fov, sizeof(fov));
}
int collision(const apex_ads::CollisionQuery* query, double* output) {
    ++calls;
    last_desired = query->desired[1];
    if (blocked) return 1;
    std::memcpy(output, query->desired, sizeof(query->desired));
    return 0;
}
double frame(Manager& manager, float delta) {
    View view;
    using Update = void (*)(void*, void*, float);
    reinterpret_cast<Update>(manager.table[apex_view::update_slot])(&manager, &view, delta);
    double result;
    std::memcpy(&result, view.data + apex_view::view_location_offset + 8, sizeof(result));
    return result;
}
bool close_to(double a, double b) { return std::abs(a - b) < 0.0001; }

int main() {
    auto* table = static_cast<void**>(VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
    check(table != nullptr);
    table[apex_view::update_slot] = reinterpret_cast<void*>(&native_update);
    Manager manager{table};
    const auto module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    apex_view::Config config{apex_view::VIEW_TARGET_ABI, 0, apex_view::update_slot, 0,
        reinterpret_cast<uintptr_t>(&native_update) - module, 35, 5};
    check(view_set_transition_duration(0.5) != 0);
    check(view_start(&manager, &config) == 0);
    check(view_set_collision(&collision) == 0);
    check(close_to(frame(manager, 0), 55));
    check(view_set_transition_duration(0.4) == 0 && view_set_right(-35));
    check(close_to(frame(manager, 0), 55));
    check(close_to(frame(manager, 0.2f), 20));
    check(close_to(frame(manager, 0.2f), -15));
    check(view_set_climb_suspended(1) == 0);
    check(close_to(frame(manager, 0), -15));
    check(close_to(frame(manager, 0.233f), 20));
    check(view_set_climb_suspended(0) == 0);
    check(view_set_transition_duration(0) == 0);
    // Shoulder smoothing off cannot cancel a native-climb return.
    check(close_to(frame(manager, 0.1165f), 2.5));
    check(close_to(frame(manager, 0.1165f), -15));
    check(view_set_transition_duration(0.5) == 0 && view_set_right(35));
    blocked = true;
    check(close_to(frame(manager, 0.25f), 20));
    check(close_to(last_desired, 20)); // The intermediate position reaches physics, never a post-collision lerp.
    blocked = false;
    check(view_set_climb_suspended(1) == 0);
    check(view_set_suspended(1) == 0);
    const int before = calls;
    check(close_to(frame(manager, 0.1f), 20) && calls == before);
    check(view_set_suspended(0) == 0 && close_to(frame(manager, 0), 55));
    check(view_set_offset_suspended(1, 0.4) == 0);
    check(view_offset_transition_active());
    check(close_to(frame(manager, 0), 55));
    check(close_to(frame(manager, 0.2f), 37.5));
    check(close_to(last_desired, 37.5));
    check(close_to(frame(manager, 0.2f), 20));
    check(!view_offset_transition_active());
    check(view_set_offset_suspended(0, 0.4) == 0);
    check(close_to(frame(manager, 0.2f), 37.5));
    check(close_to(frame(manager, 0.2f), 55));
    check(view_set_offset_suspended(1, 0) == 0);
    check(close_to(frame(manager, 0), 20));
    check(view_set_offset_suspended(0, 0) == 0);
    check(close_to(frame(manager, 0), 55));
    check(view_set_offset_suspended(2, 0.2) != 0);
    check(view_set_offset_suspended(1, -1) != 0);
    check(view_set_transition_duration(-1) != 0);
    check(view_set_transition_duration(std::numeric_limits<double>::quiet_NaN()) != 0);
    int foreign = 0;
    std::thread worker([&] { foreign = view_set_climb_suspended(1); });
    worker.join();
    check(foreign != 0);
    check(view_stop() == 0);
    check(view_start(&manager, &config) == 0 && view_set_collision(&collision) == 0);
    check(close_to(frame(manager, 0), 55));
    check(view_stop() == 0 && VirtualFree(table, 0, MEM_RELEASE));
    std::cout << "RESULTAT: OK - real camera transitions before collision and authority cancellation\n";
}

#include "view_target_bridge.h"
#include "ads_api.h"
#include "ads_native_test_fixture.h"
#include "ads_test_assert.h"
#include "framing_view.h"
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>

using namespace apex_view;
namespace {
struct ViewTarget { alignas(16) unsigned char bytes[80]{}; };
enum class Collision { accepted, refused, clipped, stopped };
Collision response{};
apex_ads::CollisionQuery observed{};

__declspec(noinline) void original_update(void*, void* raw_view, float) {
    auto& view = *static_cast<ViewTarget*>(raw_view);
    const double position[] = {5, 0, 0};
    const float fov = 90;
    std::memcpy(view.bytes + view_location_offset, position, sizeof(position));
    std::memcpy(view.bytes + apex_ads::FOV_OFFSET, &fov, sizeof(fov));
}
int resolve_collision(const apex_ads::CollisionQuery* query, double* output) {
    observed = *query;
    Stats live{};
    assert(view_stats(&live) == 0);
    // An unaccepted location must remain unobservable while physics runs.
    assert(live.after[0] == 5 && live.after[1] == 0 && live.after[2] == 0);
    if (response == Collision::stopped) assert(view_stop() == 0);
    if (response == Collision::refused) return 1;
    std::memcpy(output, query->desired, sizeof(query->desired));
    if (response == Collision::clipped) {
        output[1] = 19.25;
        output[2] = 4.25;
    }
    return 0;
}
bool close_to(double actual, double expected) { return std::abs(actual - expected) < 1e-9; }
ViewTarget invoke(void* manager, void** table) {
    ViewTarget view{};
    reinterpret_cast<void (*)(void*, void*, float)>(table[update_slot])(manager, &view, .016f);
    return view;
}
void check(const ViewTarget& view, double y, double z, float fov = 90) {
    double position[3]{};
    float obtained{};
    std::memcpy(position, view.bytes + view_location_offset, sizeof(position));
    std::memcpy(&obtained, view.bytes + apex_ads::FOV_OFFSET, sizeof(obtained));
    assert(close_to(position[0], 5) && close_to(position[1], y) && close_to(position[2], z));
    assert(std::abs(obtained - fov) < .001f);
}
void desired_is_framed() {
    // Historical shoulder (5,35,5), body (500,0,0): 10% adds 3.5 to Y and Z.
    assert(close_to(observed.desired[0], 5));
    assert(close_to(observed.desired[1], 38.5) && close_to(observed.desired[2], 8.5));
}
}
int main() {
    apex_ads::NativeFixture fixture;
    auto* table = static_cast<void**>(VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
    assert(table);
    table[update_slot] = reinterpret_cast<void*>(&original_update);
    fixture.put(2, 0, reinterpret_cast<uintptr_t>(table));
    auto& ads = apex_ads::shared_ads();
    assert(ads.configure(fixture.table_address(), fixture.third, fixture.zoom));
    ads.set_installed(true);
    const auto module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const Config config{VIEW_TARGET_ABI, 0, update_slot, 0,
        static_cast<uint64_t>(reinterpret_cast<uintptr_t>(&original_update) - module), 35, 5};
    void* manager = fixture.manager();
    assert(view_start(manager, &config) == 0 && view_set_collision(&resolve_collision) == 0);
    auto context = fixture.framing_context();
    context.values[0] = 25; context.values[1] = 10; context.values[2] = 10;
    assert(view_set_framing(&context) == 0);
    assert(ads.publish(fixture.context(1)) == 0);

    // ADS retains its strict stable-mode guard, while position survives the normal blend.
    for (uint8_t transitioning : {uint8_t{0}, uint8_t{1}}) {
        apex_ads::NativeFixture::store(fixture.mode, apex_ads::MODE_BLEND_REMAINING_OFFSET, .25f);
        apex_ads::NativeFixture::store(fixture.mode, apex_ads::MODE_TRANSITION_FLAG_OFFSET, transitioning);
        apex_ads::Ticket ticket{};
        assert(!ads.ticket(manager, ticket));
        check(invoke(manager, table), 38.5, 8.5);
        desired_is_framed();
        assert(view_framing_status() == static_cast<uint32_t>(apex_framing::Status::applied));
        assert(!view_framing_zoom_pending());
    }
    response = Collision::refused;
    check(invoke(manager, table), 0, 0);
    desired_is_framed();
    assert(view_framing_status() == static_cast<uint32_t>(apex_framing::Status::reference_unavailable));
    assert(view_set_framing(nullptr) == 0);
    check(invoke(manager, table), 0, 0);
    assert(view_framing_status() == static_cast<uint32_t>(apex_framing::Status::disabled));
    assert(view_set_framing(&context) == 0);
    response = Collision::clipped;
    check(invoke(manager, table), 19.25, 4.25);
    desired_is_framed();

    // Stable native ADS zoom remains effective when optional progress is unavailable outside game.
    response = Collision::accepted;
    apex_ads::NativeFixture::store(fixture.mode, apex_ads::MODE_BLEND_REMAINING_OFFSET, 0.0f);
    apex_ads::NativeFixture::store(fixture.mode, apex_ads::MODE_TRANSITION_FLAG_OFFSET, uint8_t{0});
    check(invoke(manager, table), 38.5, 8.5, 53.1301f);
    desired_is_framed();
    assert(view_framing_status() == static_cast<uint32_t>(apex_framing::Status::progress_unavailable));
    assert(!view_framing_zoom_pending());
    Stats stats{};
    assert(view_stats(&stats) == 0 && stats.ads_effective == 1);
    assert(stats.calls == 6 && stats.writes == 4 && stats.rejected == 2);

    // Malformed blending data must never authorize framing or native ADS.
    for (float remaining : {-1.0f, std::numeric_limits<float>::quiet_NaN(),
                             std::numeric_limits<float>::infinity()}) {
        apex_ads::NativeFixture::store(fixture.mode, apex_ads::MODE_BLEND_REMAINING_OFFSET, remaining);
        check(invoke(manager, table), 35, 5);
        assert(view_framing_status() == static_cast<uint32_t>(apex_framing::Status::context_unavailable));
    }
    apex_ads::NativeFixture::store(fixture.mode, apex_ads::MODE_BLEND_REMAINING_OFFSET, .25f);
    apex_ads::NativeFixture::store(fixture.mode, apex_ads::MODE_TRANSITION_FLAG_OFFSET, uint8_t{2});
    check(invoke(manager, table), 35, 5);
    response = Collision::stopped;
    apex_ads::NativeFixture::store(fixture.mode, apex_ads::MODE_TRANSITION_FLAG_OFFSET, uint8_t{1});
    check(invoke(manager, table), 0, 0);
    desired_is_framed();
    assert(view_stats(&stats) == 0 && !stats.active);
    assert(table[update_slot] == reinterpret_cast<void*>(&original_update));
    assert(VirtualFree(table, 0, MEM_RELEASE));
    std::cout << "RESULTAT: OK (framing dispatch, normal blend, accepted/refused/clipped/stopped collision)\n";
}

#include "ads_view.h"
#include "ads_native_test_fixture.h"
#include <cassert>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include "ads_test_assert.h"

using namespace apex_ads;
namespace {
NativeFixture fixture;
State state;
enum class Scenario { stable, default_mode, slide, ground_slam, transition, invalid, generation };
Scenario scenario{};
int originals{}, zoom_calls{};
float factor = 0.5f;
float zoom(void*, void*, void*) { ++zoom_calls; return factor; }
void original(void*, void* view, float) {
    ++originals;
    const float fov = scenario == Scenario::stable ? 110.0f : 70.0f;
    std::memcpy(static_cast<unsigned char*>(view) + FOV_OFFSET, &fov, sizeof(fov));
    if (scenario == Scenario::default_mode) fixture.put(2, MANAGER_MODE_OFFSET, uint64_t{10});
    if (scenario == Scenario::slide) fixture.put(2, MANAGER_MODE_OFFSET, uint64_t{11});
    if (scenario == Scenario::ground_slam) fixture.put(2, MANAGER_MODE_OFFSET, uint64_t{12});
    if (scenario == Scenario::transition) NativeFixture::store(fixture.mode, MODE_BLEND_REMAINING_OFFSET, 0.2f);
    if (scenario == Scenario::invalid) fixture.put(2, MANAGER_MODE_OBJECT_OFFSET, uintptr_t{1});
    if (scenario == Scenario::generation) state.clear(state.statistics().generation);
}
void reset_mode() {
    fixture.put(2, MANAGER_MODE_OFFSET, NativeFixture::third);
    fixture.put(2, MANAGER_MODE_OBJECT_OFFSET, reinterpret_cast<uintptr_t>(fixture.mode));
    NativeFixture::store(fixture.mode, MODE_BLEND_REMAINING_OFFSET, 0.0f);
}
float read_fov(const unsigned char* view) {
    float result{};
    std::memcpy(&result, view + FOV_OFFSET, sizeof(result));
    return result;
}
}
int main() {
    assert(std::abs(zoom_fov(110.0f, 0.5f) - 71.05929f) < 0.001f);
    assert(std::abs(zoom_fov(110.0f, 0.75f) - 93.93292f) < 0.001f);
    assert(state.configure(fixture.table_address(), NativeFixture::third, &zoom));
    state.set_installed(true);
    uint64_t generation{};
    alignas(16) unsigned char view[80]{};
    for (auto next : {Scenario::stable, Scenario::default_mode, Scenario::slide,
            Scenario::ground_slam, Scenario::transition, Scenario::invalid, Scenario::generation}) {
        reset_mode();
        scenario = next;
        assert(state.publish(fixture.context(++generation)) == 0);
        const auto before = state.statistics().fov_writes;
        const int calls = originals;
        const bool changed = update_view(state, fixture.manager(), view, 0.016f, &original);
        assert(originals == calls + 1);
        assert(changed == (next == Scenario::stable));
        assert(state.statistics().fov_writes == before + (changed ? 1 : 0));
        assert(std::abs(read_fov(view) - (changed ? 71.05929f : 70.0f)) < 0.001f);
        state.clear(generation);
    }
    reset_mode(); scenario = Scenario::stable;
    assert(state.publish(fixture.context(++generation)) == 0);
    assert(update_view(state, fixture.manager(), view, 0.016f, &original));
    const float first = read_fov(view);
    assert(update_view(state, fixture.manager(), view, 0.016f, &original));
    assert(read_fov(view) == first); // Each original supplies a new unzoomed view.
    assert(state.release(generation) == 0);
    for (float tail : {0.5f, 0.75f, 1.0f}) {
        factor = tail;
        assert(update_view(state, fixture.manager(), view, 0.016f, &original));
        const float expected = tail == 0.5f ? 71.05929f : tail == 0.75f ? 93.93292f : 110.0f;
        assert(std::abs(read_fov(view) - expected) < 0.001f);
    }
    state.clear(generation);
    assert(!update_view(state, fixture.manager(), view, 0.016f, &original));
    for (float invalid : {0.0f, -1.0f, 3.0f, std::numeric_limits<float>::infinity(),
                          std::numeric_limits<float>::quiet_NaN()}) {
        state.clear(generation);
        assert(state.publish(fixture.context(++generation)) == 0);
        factor = invalid;
        assert(!update_view(state, fixture.manager(), view, 0.016f, &original));
        assert(read_fov(view) == 110.0f);
    }
    assert(zoom_calls > 0);
    std::cout << "RESULTAT: OK (real ADS wrapper; no double or cumulative zoom)\n";
}

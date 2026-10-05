#include "framing_view.h"
#include "framing_math.h"
#include "ads_native_test_fixture.h"
#include "ads_test_assert.h"
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <thread>

using namespace apex_ads;
using namespace apex_framing;
bool progress(void*, void*, float& value) { value = 1.0f; return true; }
bool unavailable(void*, void*, float&) { return false; }
float tested_alpha = 0;
bool sampled_progress(void*, void*, float& value) { value = tested_alpha; return true; }

void zoom_preserves_aim_ray(State& state, FramingContext context, void* manager) {
    // An unchanged origin and orientation keep every point on the central ray
    // centered, both near and far. The FOV alone controls magnification.
    for (Vec3 rotation : {Vec3{0, 0, 0}, {35, 30, 15}, {-30, -20, -45}}) {
        for (double side : {-50.0, 50.0}) {
            for (int horizontal : {0, 10, 50}) {
                for (int height : {-50, 0, 50}) {
                    context.values[1] = horizontal; context.values[2] = height;
                    Vec3 reference{};
                    for (int zoom : {0, 15, 25, 50}) {
                        context.values[0] = zoom;
                        for (float alpha : {0.0f, .25f, .5f, 1.0f, .75f, .25f, 0.0f}) {
                            alignas(16) unsigned char view[80]{};
                            const float base_fov = 90;
                            std::memcpy(view + FOV_OFFSET, &base_fov, sizeof(base_fov));
                            std::memcpy(view + apex_view::view_rotation_offset, &rotation, sizeof(rotation));
                            apex_view::Stats stats{};
                            stats.after[1] = side; stats.after[2] = 60;
                            tested_alpha = alpha;
                            assert(apply(state, context, manager, view, stats, true, true,
                                         sampled_progress) == Status::applied);
                            Vec3 location{}, obtained_rotation{};
                            float fov{};
                            std::memcpy(&location, view + apex_view::view_location_offset, sizeof(location));
                            std::memcpy(&obtained_rotation, view + apex_view::view_rotation_offset, sizeof(rotation));
                            std::memcpy(&fov, view + FOV_OFFSET, sizeof(fov));
                            if (zoom == 0) reference = location;
                            assert(std::abs(location.x - reference.x) < 1e-9);
                            assert(std::abs(location.y - reference.y) < 1e-9);
                            assert(std::abs(location.z - reference.z) < 1e-9);
                            assert(std::memcmp(&rotation, &obtained_rotation, sizeof(rotation)) == 0);
                            const double magnification = 1.0 / std::tan(fov * std::acos(-1.0) / 360);
                            assert(std::abs(magnification - (1.0 + zoom / 100.0 * alpha)) < 1e-6);
                        }
                    }
                }
            }
        }
    }
}

int main() {
    NativeFixture fixture;
    State state;
    assert(state.configure(fixture.table_address(), fixture.third, fixture.zoom));
    auto context = fixture.framing_context();
    assert(valid(context));
    zoom_preserves_aim_ray(state, context, fixture.manager());
    alignas(16) unsigned char view[80]{};
    auto reset = [&] {
        std::memset(view, 0, sizeof(view));
        const float fov = 90;
        std::memcpy(view + FOV_OFFSET, &fov, sizeof(fov));
    };
    apex_view::Stats stats{};
    stats.after[1] = 50;
    reset();
    assert(apply(state, context, fixture.manager(), view, stats, true, true, progress) == Status::applied);
    float fov{};
    std::memcpy(&fov, view + FOV_OFFSET, sizeof(fov));
    assert(fov == 90 && stats.after[1] == 50);
    context.values[0] = 25; context.values[1] = 10; context.values[2] = 10;
    stats.after[1] = 50;
    reset();
    bool pending{};
    assert(apply(state, context, fixture.manager(), view, stats, true, true, progress, &pending) == Status::applied);
    assert(pending);
    std::memcpy(&fov, view + FOV_OFFSET, sizeof(fov));
    assert(std::abs(fov - 77.3196f) < 0.001f);
    assert(std::abs(stats.after[1] - 55) < 1e-9 && std::abs(stats.after[2] - 5) < 1e-9);
    // Preview still exposes the full collision segment, but writes nothing.
    reset(); stats.after[1] = 50; stats.after[2] = 0;
    assert(apply(state, context, fixture.manager(), view, stats, true, false, progress) == Status::applied);
    std::memcpy(&fov, view + FOV_OFFSET, sizeof(fov));
    assert(fov == 90 && std::abs(stats.after[1] - 55) < 1e-9);
    // Progress failure rejects only extra zoom; independent framing remains collision-ready.
    reset(); stats.after[1] = 50; stats.after[2] = 0;
    pending = true;
    assert(apply(state, context, fixture.manager(), view, stats, true, true, unavailable, &pending) == Status::progress_unavailable);
    std::memcpy(&fov, view + FOV_OFFSET, sizeof(fov));
    assert(fov == 90 && !pending);
    assert(std::abs(stats.after[1] - 55) < 1e-9 && std::abs(stats.after[2] - 5) < 1e-9);
    for (float invalid : {-1.0f, 1.01f, std::numeric_limits<float>::quiet_NaN(),
                           std::numeric_limits<float>::infinity()}) {
        reset(); stats.after[1] = 50; stats.after[2] = 0;
        tested_alpha = invalid;
        assert(apply(state, context, fixture.manager(), view, stats, true, true,
                     sampled_progress, &pending) == Status::progress_unavailable);
        Vec3 location{};
        std::memcpy(&location, view + apex_view::view_location_offset, sizeof(location));
        std::memcpy(&fov, view + FOV_OFFSET, sizeof(fov));
        assert(fov == 90 && !pending && std::abs(location.y - 55) < 1e-9
               && std::abs(location.z - 5) < 1e-9);
    }
    // Hip framing needs no weapon progress.
    assert(apply(state, context, fixture.manager(), view, stats, false, true, unavailable) == Status::applied);
    // A degenerate lateral projection does not invalidate an independently guarded FOV.
    reset(); stats.after[0] = stats.after[1] = stats.after[2] = 0;
    assert(static_cast<uint32_t>(apply(state, context, fixture.manager(), view, stats,
                                    true, true, progress, &pending)) == 6);
    std::memcpy(&fov, view + FOV_OFFSET, sizeof(fov));
    assert(std::abs(fov - 77.3196f) < 0.001f && pending);
    Vec3 unchanged{};
    std::memcpy(&unchanged, view + apex_view::view_location_offset, sizeof(unchanged));
    assert(unchanged.x == 0 && unchanged.y == 0 && unchanged.z == 0);
    fixture.recycle(5);
    assert(!state.framing_allowed(context, fixture.manager()));
    fixture.restore(5);
    fixture.put(5, context.parent_offset, fixture.pointer(1));
    assert(apply(state, context, fixture.manager(), view, stats, false, true, progress) == Status::body_unavailable);
    reset();
    assert(apply(state, context, fixture.manager(), view, stats, true, true, progress) == Status::body_unavailable);
    std::memcpy(&fov, view + FOV_OFFSET, sizeof(fov));
    assert(fov == 90); // Attached bodies cannot qualify either optional setting safely.
    fixture.put(5, context.parent_offset, uintptr_t{});
    bool foreign = true;
    std::thread worker([&] { foreign = state.framing_allowed(context, fixture.manager()); });
    worker.join(); assert(!foreign);
    fixture.put(2, MANAGER_MODE_OFFSET, uint64_t{99});
    assert(!state.framing_allowed(context, fixture.manager()));
    context.values[0] = 51; assert(!valid(context));
    std::cout << "RESULTAT: OK - framing transaction, live body, exclusions, collision preview\n";
}

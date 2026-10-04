#include "ads_reticle.h"
#include "ads_native_test_fixture.h"
#include <cassert>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <thread>
#include "ads_test_assert.h"

using namespace apex_ads;
namespace {
NativeFixture fixture;
State state;
Reticle reticle(state);
constexpr uintptr_t caller = 0x10000;
int producer_calls{}, getter_calls{};
bool observed{}, nested_observed{};
enum class Scenario { normal, nested, clear, release, failure };
Scenario scenario{};
bool original_getter(void*) { ++getter_calls; return false; }
void original_producer(void* collector, void* weapon) {
    ++producer_calls;
    if (scenario == Scenario::failure) throw std::runtime_error("game exception");
    if (scenario == Scenario::nested) {
        scenario = Scenario::normal;
        reticle.producer(collector, weapon);
        nested_observed = observed;
        scenario = Scenario::nested;
    }
    if (scenario == Scenario::clear) state.clear(state.statistics().generation);
    if (scenario == Scenario::release) assert(state.release(state.statistics().generation) == 0);
    observed = reticle.getter(weapon, caller);
}
}
int main() {
    assert(state.configure(fixture.table_address(), NativeFixture::third, &NativeFixture::zoom));
    state.set_installed(true);
    assert(reticle.configure(&original_producer, &original_getter, caller));
    uint64_t generation = 1;
    assert(state.publish(fixture.context(generation)) == 0);
    unsigned char weapon_before[sizeof(fixture.objects[3])];
    std::memcpy(weapon_before, fixture.objects[3], sizeof(weapon_before));
    reticle.producer(fixture.collector(), fixture.objects[3]);
    assert(observed && producer_calls == 1 && getter_calls == 1);
    assert(state.statistics().reticle_writes == 1);
    const auto written = state.statistics().reticle_writes;
    scenario = Scenario::release;
    reticle.producer(fixture.collector(), fixture.objects[3]);
    assert(!observed && state.statistics().reticle_writes == written);
    assert(!state.statistics().pending);
    Ticket tail{};
    assert(state.ticket(fixture.manager(), tail)); // HUD is passive, but the native zoom-out remains authorized.
    state.clear(generation);
    assert(!state.current(tail));
    scenario = Scenario::normal;
    assert(state.publish(fixture.context(++generation)) == 0);
    assert(!reticle.getter(fixture.objects[3], caller));
    reticle.producer(fixture.objects[4], fixture.objects[3]);
    assert(!observed); // Foreign collector with exactly the same weapon.
    reticle.producer(fixture.collector(), fixture.objects[4]);
    assert(!observed);
    scenario = Scenario::nested;
    reticle.producer(fixture.collector(), fixture.objects[3]);
    assert(observed && !nested_observed);
    scenario = Scenario::clear;
    reticle.producer(fixture.collector(), fixture.objects[3]);
    assert(!observed && !state.statistics().pending);
    scenario = Scenario::normal;
    assert(state.publish(fixture.context(++generation)) == 0);
    scenario = Scenario::failure;
    try { reticle.producer(fixture.collector(), fixture.objects[3]); assert(false); }
    catch (const std::runtime_error&) {}
    assert(!reticle.getter(fixture.objects[3], caller)); // TLS restored after a game exception.
    scenario = Scenario::normal;
    const auto before = state.statistics().wrong_thread;
    std::thread foreign([&] {
        reticle.producer(fixture.collector(), fixture.objects[3]);
        assert(!observed);
    });
    foreign.join();
    assert(state.statistics().wrong_thread > before);
    assert(!std::memcmp(weapon_before, fixture.objects[3], sizeof(weapon_before)));
    state.clear(generation);
    reticle.producer(fixture.collector(), fixture.objects[3]);
    assert(!observed);
    std::cout << "RESULTAT: OK (real HUD wrappers, ownership, nesting, thread, cleanup)\n";
}

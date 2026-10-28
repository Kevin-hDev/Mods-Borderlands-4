#include "ads_state.h"
#include "ads_native_test_fixture.h"
#include <cassert>
#include <iostream>
#include <limits>
#include <thread>
#include "ads_test_assert.h"

using namespace apex_ads;
int main() {
    NativeFixture fixture;
    State state;
    assert(state.configure(fixture.table_address(), NativeFixture::third, &NativeFixture::zoom));
    state.set_installed(true);
    auto context = fixture.context(1);
    assert(state.publish(context) == 0);
    Ticket ticket{};
    assert(state.ticket(fixture.manager(), ticket));
    assert(state.current(ticket));
    assert(state.publish(context) != 0); // A reused generation invalidates the prior permission.
    assert(!state.current(ticket));
    context.generation = 2;
    assert(state.publish(context) == 0);
    auto stats = state.statistics();
    std::thread foreign([&] { Ticket other{}; assert(!state.ticket(fixture.manager(), other)); });
    foreign.join();
    assert(state.statistics().wrong_thread == stats.wrong_thread + 1);
    assert(state.ticket(fixture.manager(), ticket));
    fixture.recycle(3);
    assert(!state.current(ticket));
    assert(state.statistics().identity_refused != 0);
    fixture.restore(3);
    context.generation = 3;
    assert(state.publish(context) == 0);
    assert(state.ticket(fixture.manager(), ticket));
    fixture.put(4, ANIMATION_WEAPON_OFFSET, uintptr_t{0});
    const auto identity_refusals = state.statistics().identity_refused;
    assert(!state.current(ticket));
    assert(state.statistics().error == ERROR_CONTEXT);
    assert(state.statistics().identity_refused == identity_refusals);
    assert(state.clear(context.generation) == 0);
    assert(!state.ticket(fixture.manager(), ticket));
    fixture.put(4, ANIMATION_WEAPON_OFFSET, fixture.pointer(3));
    context.generation = 4;
    assert(state.publish(context) == 0);
    assert(state.ticket(fixture.manager(), ticket));
    state.record_reticle(ticket);
    assert(state.release(4) == 0 && state.statistics().pending);
    assert(state.current(ticket));
    assert(!state.reticle_current(ticket));
    assert(state.clear(4) == 0 && state.statistics().pending);
    assert(state.publish(fixture.context(5)) != 0); // A transfer cannot hide unfinished cleanup.
    state.restored(fixture.collector());
    assert(!state.statistics().pending);
    assert(state.statistics().restorations == 1);
    assert(state.publish(fixture.context(6)) == 0);
    assert(state.publish_pointer(reinterpret_cast<const AdsContext*>(1)) != 0);
    assert(!state.statistics().active);
    assert(state.publish(fixture.context(7)) == 0);
    assert(state.ticket(fixture.manager(), ticket));
    state.record_reticle(ticket);
    state.clear(7);
    fixture.recycle(1);
    state.clear(7);
    assert(!state.statistics().pending && state.statistics().error == ERROR_IDENTITY);
    fixture.restore(1);
    assert(state.publish(fixture.context(8)) == 0);
    assert(state.ticket(fixture.manager(), ticket));
    state.record_reticle(ticket);
    state.clear(8);
    fixture.put(0, apex_interaction::pawn_offset, uintptr_t{0});
    state.clear(8);
    assert(!state.statistics().pending && state.statistics().error == ERROR_CONTEXT);
    fixture.put(0, apex_interaction::pawn_offset, fixture.pointer(1));
    assert(state.publish(fixture.context(9)) == 0);
    state.note_error(static_cast<uint32_t>(ERROR_IDENTITY));
    assert(state.clear(9) == 0);
    assert(state.statistics().error == 0); // A live cleanup must not inherit a prior refusal.
    context = fixture.context(UINT64_MAX);
    assert(state.publish(context) != 0);
    fixture.put(4, ANIMATION_CATEGORY_OFFSET, static_cast<uint8_t>(CATEGORY_SNIPER));
    assert(state.publish(fixture.context(10)) == 0);
    fixture.put(4, ANIMATION_CATEGORY_OFFSET, static_cast<uint8_t>(CATEGORY_HEAVY));
    assert(state.publish(fixture.context(11)) == 0);
    fixture.put(4, ANIMATION_CATEGORY_OFFSET, static_cast<uint8_t>(CATEGORY_MAX));
    assert(state.publish(fixture.context(12)) != 0 && state.statistics().error == ERROR_CONTEXT);
    fixture.put(4, ANIMATION_CATEGORY_OFFSET, static_cast<uint8_t>(CATEGORY_ASSAULT));
    assert(state.publish(fixture.context(12)) == 0);
    Ticket optic_ticket{};
    assert(state.ticket(fixture.manager(), optic_ticket) && state.optic(optic_ticket) == 0.0f);
    assert(state.set_optic(11, 0.5f) != 0); // Only the published aim takes an optic.
    for (float invalid : {-0.1f, 1.5f, std::numeric_limits<float>::quiet_NaN()}) {
        assert(state.set_optic(12, invalid) != 0);
    }
    assert(state.set_optic(12, 0.125f) == 0 && state.optic(optic_ticket) == 0.125f);
    assert(state.release(12) == 0 && state.set_optic(12, 1.0f) == 0 && state.optic(optic_ticket) == 1.0f);
    std::thread optic_foreign([&] { assert(state.set_optic(12, 0.5f) != 0); });
    optic_foreign.join();
    assert(state.optic(optic_ticket) == 1.0f);
    assert(state.clear(12) == 0 && state.set_optic(12, 0.5f) != 0);
    assert(state.publish(fixture.context(13)) == 0);
    assert(state.ticket(fixture.manager(), optic_ticket) && state.optic(optic_ticket) == 0.0f);
    std::cout << "RESULTAT: OK (ADS state, generation, identity and thread)\n";
}

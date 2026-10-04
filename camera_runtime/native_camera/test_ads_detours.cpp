#include "ads_detours.h"
#include "ads_native_test_fixture.h"
#include <cassert>
#include <cstring>
#include <iostream>
#include "ads_test_assert.h"

using namespace apex_ads;
namespace {
int calls{}, refused{};
bool pin(void*) { return true; }
void native_producer(void*, void*) {}
bool native_getter(void*) { return false; }
bool install(uintptr_t, void*, void** original, const char*, size_t) {
    ++calls;
    void* address = calls == 1 ? reinterpret_cast<void*>(&native_getter)
                              : reinterpret_cast<void*>(&native_producer);
    std::memcpy(original, &address, sizeof(address));
    return calls != refused; // Even failure can have supplied a trampoline.
}
}
int main() {
    NativeFixture fixture;
    for (int failure : {1, 2, 0}) {
        State state;
        assert(state.configure(fixture.table_address(), NativeFixture::third, &NativeFixture::zoom));
        Reticle reticle(state);
        Detours detours;
        calls = 0; refused = failure;
        DetourBindings bindings{&install, &pin, 0x140000000, reinterpret_cast<void*>(0x10000),
                                reinterpret_cast<void*>(0x20000), false};
        assert(detours.install(state, reticle, bindings) != 0 && calls == 0);
        bindings.verified = true;
        const int result = detours.install(state, reticle, bindings);
        assert((result == 0) == (failure == 0));
        assert(calls == (failure == 1 ? 1 : 2));
        assert(state.statistics().installed == (failure == 0 ? 1U : 0U));
        const int previous = calls;
        assert(detours.install(state, reticle, bindings) == result && calls == previous);
        assert(state.statistics().install_attempts == 1);
        assert(!reticle.getter(fixture.objects[3], 0x140000000 + HUD_GETTER_RETURN_RVA));
        if (failure != 1) reticle.producer(fixture.collector(), fixture.objects[3]);
    }
    std::cout << "RESULTAT: OK (partial hooks passive; failure terminal)\n";
}

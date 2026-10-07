// Exercise the production reader with real memory validation and fake game signatures.
#include <windows.h>
#include <cassert>
#include <array>
#include <iostream>
#include "ads_test_assert.h"

namespace {
size_t queries{}, signature_calls{};
bool signature_match = true;
SIZE_T WINAPI counted_query(LPCVOID address, PMEMORY_BASIC_INFORMATION output, SIZE_T size) {
    ++queries;
    return VirtualQuery(address, output, size);
}
}
#define VirtualQuery counted_query
#include "framing_progress.cpp"
#undef VirtualQuery

namespace apex_ads {
bool signature_matches(uintptr_t, const char*) { ++signature_calls; return signature_match; }
}
namespace {
void first_method() {}
int second_method() { return 42; }
template<int Value> int distinct_method() { return Value; }
}

int main(int argc, char**) {
    assert(camera_builds::publish(1));
    using namespace apex_ads;
    signature_match = argc == 1;
    alignas(8) std::array<unsigned char, MANAGER_INPUTS_OFFSET + 8> manager{};
    float output = 0.75f;
    // No inputs: refusal must leave output untouched; fixed code is checked only once.
    for (int i = 0; i < 100; ++i) {
        assert(!apex_framing::native_progress(manager.data(), manager.data(), output));
        assert(output == 0.75f);
    }
    assert(signature_calls == (signature_match ? 2U : 1U));
    if (!signature_match) {
        signature_match = true;
        assert(!apex_framing::native_progress(manager.data(), manager.data(), output));
        assert(signature_calls == 1); // A refused build cannot become trusted by retrying.
    }
    void* slots[] = {reinterpret_cast<void*>(&first_method)};
    void** object = slots;
    assert(virtual_at(&object, 0) == slots[0]);
    const size_t first_queries = queries;
    for (int i = 0; i < 100; ++i) assert(virtual_at(&object, 0) == slots[0]);
    // Object and slot remain freshly checked; executable-address qualification is reused.
    assert(queries - first_queries == 200);
    slots[0] = reinterpret_cast<void*>(&second_method);
    const size_t before_swap = queries;
    assert(virtual_at(&object, 0) == slots[0]);
    assert(queries - before_swap == 3);
    slots[0] = &object;
    assert(virtual_at(&object, 0) == nullptr); // Data is never callable code.
    auto* foreign = VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    assert(foreign);
    slots[0] = foreign;
    assert(virtual_at(&object, 0) == nullptr); // Executable outside the main image is refused.
    assert(VirtualFree(foreign, 0, MEM_RELEASE));
    object = nullptr;
    assert(virtual_at(&object, 0) == nullptr); // A cached method never retains its object.
    apex_framing::ExecutableCache bounded;
    void* methods[] = {reinterpret_cast<void*>(&distinct_method<0>),
        reinterpret_cast<void*>(&distinct_method<1>), reinterpret_cast<void*>(&distinct_method<2>),
        reinterpret_cast<void*>(&distinct_method<3>), reinterpret_cast<void*>(&distinct_method<4>),
        reinterpret_cast<void*>(&distinct_method<5>), reinterpret_cast<void*>(&distinct_method<6>),
        reinterpret_cast<void*>(&distinct_method<7>), reinterpret_cast<void*>(&distinct_method<8>)};
    for (auto* method : methods) assert(bounded.accepts(method));
    const auto before_eviction = queries;
    assert(bounded.accepts(methods[8]));
    assert(queries == before_eviction);
    assert(bounded.accepts(methods[0])); // Oldest entry was evicted and must be checked again.
    assert(queries == before_eviction + 1);
    std::cout << "RESULTAT: progress qualification reused; live slots and refusals preserved\n";
}

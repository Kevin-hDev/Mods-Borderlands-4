#include "ads_identity.h"
#include "generated_ads.h"
#include <cstring>
#include <cstdlib>
#include <iostream>
#include <windows.h>

#define check(x) do { if (!(x)) { std::cerr << "RESULTAT: ECHEC line=" << __LINE__ << "\n"; std::exit(1); } } while(false)

namespace {
alignas(8) unsigned char object[64]{}, registry[64]{}, item[24]{};
void* chunk[1]{item};

template<class T> void set(unsigned char* memory, size_t offset, T value) {
    std::memcpy(memory + offset, &value, sizeof(value));
}
}

int main() {
    using namespace apex_ads;
    set(registry, 0x10, static_cast<void*>(chunk));
    set(registry, 0x24, int32_t{1});
    set(object, 0xc, int32_t{0});
    set(item, 0, static_cast<void*>(object));
    set(item, 0x10, int32_t{7});
    ObjectId identity{};
    uintptr_t resolved{};
    const auto table = reinterpret_cast<uintptr_t>(registry);
    check(capture_id(table, reinterpret_cast<uintptr_t>(object), identity));
    check(identity.serial == 7 && identity.index == 0);
    check(resolve_id(table, identity, resolved) && resolved == identity.address);
    set(item, 0x10, int32_t{8});
    check(!resolve_id(table, identity, resolved) && resolved == 0);
    set(item, 0x10, int32_t{7});
    set(item, 8, uint32_t{0x10200000});
    check(!resolve_id(table, identity, resolved));
    set(item, 8, uint32_t{0});
    identity.index = -1;
    check(!resolve_id(table, identity, resolved));
    identity.index = 1;
    check(!resolve_id(table, identity, resolved));
    identity.index = 0;
    identity.serial = 0;
    check(!resolve_id(table, identity, resolved));
    identity.serial = 7;
    chunk[0] = nullptr;
    check(!resolve_id(table, identity, resolved));
    chunk[0] = item;
    set(registry, 0x24, int32_t{0x7fffffff});
    check(!resolve_id(table, identity, resolved));
    set(registry, 0x24, int32_t{1});
    auto* inaccessible = VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_NOACCESS);
    check(inaccessible != nullptr);
    check(!resolve_id(reinterpret_cast<uintptr_t>(inaccessible), identity, resolved));
    check(!capture_id(table, reinterpret_cast<uintptr_t>(inaccessible), identity));
    check(VirtualFree(inaccessible, 0, MEM_RELEASE));
    std::cout << "RESULTAT: OK (stale object identity refused)\n";
}

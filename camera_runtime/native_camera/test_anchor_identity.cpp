#include "anchor_contract.h"
#include <array>
#include <cstring>
#include <cstdio>
#include <windows.h>

namespace {
using namespace climb_anchor;
alignas(16) unsigned char objects[reference_count][16000]{};
alignas(16) unsigned char registry[64]{}, items[reference_count * 24]{}, mode[3000]{};
void* chunks[1]{items};
void* component_table[154]{};
bool socket_exists = true;
bool has_socket(void* target, uint64_t name) {
    return socket_exists && target == objects[component] && name == 27;
}
template<class T> void set(void* p, size_t offset, T value) {
    std::memcpy(static_cast<unsigned char*>(p) + offset, &value, sizeof(value));
}
int failures{};
void check(bool result, const char* label) {
    if (!result) { ++failures; std::printf("FAIL: %s\n", label); }
}
Session fixture() {
    using namespace apex_ads;
    Session result{};
    component_table[153] = reinterpret_cast<void*>(&has_socket);
    set(objects[component], 0, component_table);
    set(registry, 0x10, chunks); set(registry, 0x24, int32_t{reference_count});
    for (size_t i = 0; i < reference_count; ++i) {
        set(objects[i], OBJECT_INDEX_OFFSET, static_cast<int32_t>(i));
        set(items, i * 24, objects[i]); set(items, i * 24 + 16, int32_t{19});
        result.references[i] = {reinterpret_cast<uintptr_t>(objects[i]), static_cast<int32_t>(i), 19};
    }
    set(objects[manager], MANAGER_STATE_OFFSET, objects[state]);
    set(objects[manager], MANAGER_INPUTS_OFFSET, objects[inputs]);
    set(objects[state], STATE_INPUTS_OFFSET, objects[inputs]);
    set(objects[inputs], INPUTS_CONTROLLER_OFFSET, objects[controller]);
    set(objects[inputs], component_offset, objects[component]);
    set(objects[inputs], 0xF8, uint64_t{0});  // Observed in the live ThirdPerson camera.
    set(objects[controller], CONTROLLER_MANAGER_OFFSET, objects[manager]);
    set(objects[controller], pawn_offset, objects[actor]);
    set(objects[manager], MANAGER_MODE_OFFSET, uint64_t{57});
    set(objects[manager], MANAGER_MODE_OBJECT_OFFSET, mode);
    result.table = reinterpret_cast<uintptr_t>(registry);
    result.thread = GetCurrentThreadId(); result.deadline = GetTickCount64() + 60000;
    result.mode_name = 57; result.socket_name = 27;
    return result;
}
}
int main() {
    using namespace climb_anchor;
    const auto sdk = LoadLibraryW(L"anchor_test_sdk/unrealsdk.dll");
    if (!sdk) { std::printf("FAIL: test SDK boundary unavailable\n"); return 1; }
    const auto setter = GetProcAddress(sdk, "set_test_object_table");
    using SetTable = void (*)(void*);
    SetTable set_table{};
    static_assert(sizeof(set_table) == sizeof(setter));
    std::memcpy(&set_table, &setter, sizeof(set_table));
    if (!set_table) { std::printf("FAIL: test registry setter unavailable\n"); return 1; }
    auto session = fixture();
    set_table(registry);
    Session captured{};
    check(capture(reinterpret_cast<uintptr_t>(objects[manager]), captured),
          "real startup captures context with empty default and existing animated Camera bone");
    check(captured.socket_name == 27 && captured.mode_name == 57,
          "startup resolves explicit bone and climb mode through SDK boundary");
    check(*reinterpret_cast<uint64_t*>(objects[inputs] + 0xF8) == 0,
          "startup never changes the game's empty default socket");
    socket_exists = false;
    check(!capture(reinterpret_cast<uintptr_t>(objects[manager]), captured),
          "startup refuses a skeleton without the selected bone");
    socket_exists = true;
    check(eligible(session, objects[state]), "owned stable climb accepted");
    check(!eligible(session, objects[inputs]), "other state refused");
    session.thread ^= 1;
    check(!eligible(session, objects[state]), "other thread refused");
    session = fixture(); session.deadline = 0;
    check(!eligible(session, objects[state]), "expired trial refused");
    check(refresh(session) && eligible(session, objects[state]),
          "live owner renews an expired lease without reinstalling the anchor");
    session.thread ^= 1;
    check(!refresh(session), "other thread cannot renew ownership");
    for (size_t i = 0; i < reference_count; ++i) {
        session = fixture(); session.references[i].serial = 20;
        check(!eligible(session, objects[state]), "every stale identity refused");
        check(!refresh(session), "every stale identity refuses lease renewal");
    }
    session = fixture(); set(objects[manager], apex_ads::MANAGER_MODE_OFFSET, uint64_t{58});
    check(!eligible(session, objects[state]), "other camera mode refused");
    check(refresh(session) && !eligible(session, objects[state]),
          "lease renewal never permits another camera mode");
    session = fixture(); set(mode, apex_ads::MODE_BLEND_REMAINING_OFFSET, 0.2f);
    check(!eligible(session, objects[state]), "native camera blend left unchanged");
    set(mode, apex_ads::MODE_BLEND_REMAINING_OFFSET, 0.0f);
    session = fixture(); set(objects[controller], pawn_offset, objects[component]);
    check(!eligible(session, objects[state]), "changed pawn refused");
    session = fixture(); set(objects[inputs], component_offset, objects[actor]);
    check(!eligible(session, objects[state]), "changed animated component refused");
    check(!refresh(session), "changed component refuses lease renewal");
    session = fixture(); set(objects[inputs], 0xF8, uint64_t{28});
    check(eligible(session, objects[state]), "unused default socket does not override explicit bone");
    session = fixture(); socket_exists = false;
    check(!eligible(session, objects[state]), "missing socket must not count native eye fallback as correction");
    std::printf("RESULTAT: %d failure(s)\n", failures);
    return failures ? 1 : 0;
}

#include "ads_api.h"
#include "camera_builds.h"
#include "ads_compat.h"
#include "ads_detours.h"
#include "ads_identity.h"
#include "ads_memory.h"
#include "ads_sdk_exports.h"
#include <intrin.h>

namespace {
apex_ads::State state;
apex_ads::Reticle reticle(state);
apex_ads::Detours detours;
volatile LONG preparation{};
int outcome = static_cast<int>(apex_ads::ERROR_UNSUPPORTED);
DWORD owning_thread{};
uintptr_t object_table{};

template<class Function> Function sdk_symbol(const char* name) {
    const auto sdk = GetModuleHandleW(apex_ads::sdk_exports::module);
    const auto symbol = sdk ? GetProcAddress(sdk, name) : nullptr;
    Function result{};
    static_assert(sizeof(result) == sizeof(symbol), "SDK export function size");
    std::memcpy(&result, &symbol, sizeof(result));
    return result;
}
bool third_name(uint64_t& output) {
    using Init = void (*)(uint64_t*, const wchar_t*, uint32_t);
    const auto initialize = sdk_symbol<Init>(apex_ads::sdk_exports::fname_init);
    if (!initialize) return false;
    __try {
        initialize(&output, L"ThirdPerson", 0);
        return output != 0;
    } __except(EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}
bool pin(void* address) {
    HMODULE pinned{};
    return GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                             reinterpret_cast<LPCWSTR>(address), &pinned) != 0;
}
void producer(void* collector, void* weapon) { reticle.producer(collector, weapon); }
bool getter(void* weapon) {
    const auto caller = reinterpret_cast<uintptr_t>(_ReturnAddress());
    return reticle.getter(weapon, caller);
}
int initialize() {
    using namespace apex_ads;
    const int compatibility = compatible_modules_error();
    if (compatibility) return compatibility;
    uint64_t name{};
    const auto install = sdk_symbol<Detour>(sdk_exports::detour);
    using Export = void (*)();
    if (!install || !sdk_symbol<Export>(sdk_exports::fname_init)
            || !sdk_symbol<Export>(sdk_exports::gobjects)) return static_cast<int>(ERROR_SDK_EXPORT);
    object_table = sdk_object_table();
    if (!object_table) return static_cast<int>(ERROR_OBJECT_TABLE);
    const auto game = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if (!third_name(name)
            || !state.configure(object_table, name, reinterpret_cast<ZoomScale>(game + camera_builds::rva(ZOOM_SCALE_RVA)))) {
        return static_cast<int>(ERROR_UNSUPPORTED);
    }
    owning_thread = GetCurrentThreadId();
    const DetourBindings bindings{install, &pin, game, reinterpret_cast<void*>(&getter),
                                  reinterpret_cast<void*>(&producer), true};
    return detours.install(state, reticle, bindings);
}
}

namespace apex_ads { State& shared_ads() { return state; } }

int ads_verify_files() {
    try { return apex_ads::verify_module_files_error(); }
    catch (...) { return static_cast<int>(apex_ads::ERROR_UNSUPPORTED); }
}

int ads_prepare() {
    const LONG previous = InterlockedCompareExchange(&preparation, 1, 0);
    if (previous) return previous == 2 ? outcome : static_cast<int>(apex_ads::ERROR_INSTALL);
    try { outcome = initialize(); }
    catch (...) { outcome = static_cast<int>(apex_ads::ERROR_UNSUPPORTED); }
    if (outcome) state.note_error(static_cast<uint32_t>(outcome));
    InterlockedExchange(&preparation, 2);
    return outcome;
}

int ads_identify(uint64_t address, apex_ads::ObjectId* output) {
    apex_ads::ObjectId identity{};
    if (!apex_ads::write_memory(reinterpret_cast<uintptr_t>(output), 0, identity)) return 1;
    if (InterlockedCompareExchange(&preparation, 0, 0) != 2 || outcome) return 1;
    if (GetCurrentThreadId() != owning_thread) {
        state.note_error(static_cast<uint32_t>(apex_ads::ERROR_WRONG_THREAD));
        return 1;
    }
    return apex_ads::capture_id(object_table, address, identity)
        && apex_ads::write_memory(reinterpret_cast<uintptr_t>(output), 0, identity) ? 0 : 1;
}

int ads_publish(const apex_ads::AdsContext* input) {
    if (InterlockedCompareExchange(&preparation, 0, 0) != 2 || outcome) return 1;
    return state.publish_pointer(input);
}

int ads_clear(uint64_t generation) { return state.clear(generation); }
int ads_release(uint64_t generation) { return state.release(generation); }

int ads_set_optic(uint64_t generation, float scale) {
    if (InterlockedCompareExchange(&preparation, 0, 0) != 2 || outcome) return 1;
    return state.set_optic(generation, scale);
}

int ads_heavy_aim() { return 0; }

int ads_stats(apex_ads::AdsStats* output) {
    const auto result = state.statistics();
    return apex_ads::write_memory(reinterpret_cast<uintptr_t>(output), 0, result) ? 0 : 1;
}

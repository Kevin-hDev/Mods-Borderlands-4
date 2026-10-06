#include "anchor_contract.h"
#include "ads_compat.h"
#include "ads_memory.h"
#include "camera_memory.h"

namespace {
SRWLOCK guard = SRWLOCK_INIT;
climb_anchor::Session session{};
climb_anchor::Statistics statistics{};
climb_anchor::Update original{}, socket_update{};
void** slot{};
thread_local bool inside = false;

void dispatch(void* behavior, void* context, void* state, float delta) {
    // Every camera keeps its native calculation unless the entire trial qualifies.
    original(behavior, context, state, delta);
    if (inside) return;
    AcquireSRWLockExclusive(&guard);
    ++statistics.calls;
    if (statistics.active && GetTickCount64() >= session.deadline) {
        statistics.active = 0; ++statistics.expired;
    }
    const bool active = statistics.active != 0;
    const auto candidate = session;
    ReleaseSRWLockExclusive(&guard);
    if (!active || !climb_anchor::eligible(candidate, state)) return;
    inside = true;
    const bool applied = climb_anchor::apply_socket(socket_update, context, state, delta, candidate.socket_name);
    inside = false;
    AcquireSRWLockExclusive(&guard);
    ++statistics.eligible;
    if (applied) ++statistics.applied;
    else { ++statistics.refused; statistics.active = 0; }
    ReleaseSRWLockExclusive(&guard);
}

int start_locked(uintptr_t manager) {
    if (statistics.installed) return 1;
    // ADS legitimately detours HUD functions before this trial starts. Qualify
    // the files and our two anchor functions, not unrelated HUD entry points.
    const int verified = apex_ads::verify_module_files_error();
    if (verified) return verified;
    const auto game = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if (!apex_ads::signature_matches(game + climb_anchor::eye_update_rva, climb_anchor::eye_prefix)
        || !apex_ads::signature_matches(game + climb_anchor::socket_update_rva, climb_anchor::socket_prefix)) return 22;
    climb_anchor::Session candidate{};
    if (!climb_anchor::capture(manager, candidate)) return 2;
    auto** target = reinterpret_cast<void**>(game + climb_anchor::eye_slot_rva);
    auto* expected = reinterpret_cast<void*>(game + climb_anchor::eye_update_rva);
    if (!apex_camera::memory_access(target, sizeof(void*)) || *target != expected) return 3;
    HMODULE pinned{};
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                           reinterpret_cast<LPCWSTR>(&dispatch), &pinned)) return 4;
    original = reinterpret_cast<climb_anchor::Update>(expected);
    socket_update = reinterpret_cast<climb_anchor::Update>(game + climb_anchor::socket_update_rva);
    session = candidate; slot = target;
    if (apex_camera::replace_slot(slot, expected, reinterpret_cast<void*>(&dispatch))) return 5;
    statistics = {}; statistics.installed = 1; statistics.active = 1;
    return 0;
}
}

int anchor_verify() { return apex_ads::verify_module_files_error(); }
int anchor_start(uint64_t manager) {
    int result = 1;
    AcquireSRWLockExclusive(&guard);
    __try {
        __try { result = start_locked(manager); }
        __except(EXCEPTION_EXECUTE_HANDLER) { result = 6; }
    } __finally { ReleaseSRWLockExclusive(&guard); }
    return result;
}
int anchor_stop() {
    AcquireSRWLockExclusive(&guard);
    statistics.active = 0;
    int result = 0;
    if (statistics.installed) {
        if (session.thread != GetCurrentThreadId()) result = 1;
        else {
            result = apex_camera::replace_slot(slot, reinterpret_cast<void*>(&dispatch),
                                               reinterpret_cast<void*>(original));
            if (!result) statistics.installed = 0;
        }
    }
    ReleaseSRWLockExclusive(&guard);
    return result;
}
int anchor_refresh() {
    AcquireSRWLockExclusive(&guard);
    int result = 1;
    __try {
        __try {
            if (statistics.installed && !statistics.refused && climb_anchor::refresh(session)) {
                statistics.active = 1;
                result = 0;
            } else { statistics.active = 0; }
        } __except(EXCEPTION_EXECUTE_HANDLER) { statistics.active = 0; result = 6; }
    } __finally { ReleaseSRWLockExclusive(&guard); }
    return result;
}
int anchor_stats(climb_anchor::Statistics* output) {
    AcquireSRWLockShared(&guard);
    const auto value = statistics;
    ReleaseSRWLockShared(&guard);
    return apex_ads::write_memory(reinterpret_cast<uintptr_t>(output), 0, value) ? 0 : 1;
}

#include "view_target_bridge.h"
#include "camera_memory.h"

#include <windows.h>

using namespace apex_view;

namespace {
using Update = void (*)(void*, void*, float);

SRWLOCK guard = SRWLOCK_INIT;
Update original = nullptr;
void** hooked_slot = nullptr;
void* target_manager = nullptr;
Config config{};
Stats stats{};
ULONGLONG deadline = 0;
bool installed = false;
bool suspended = false;

void dispatch(void* manager, void* view_target, float delta_time);

int stop_locked() {
    stats.active = 0;
    int result = 0;
    if (installed) {
        result = apex_camera::replace_slot(
            hooked_slot, reinterpret_cast<void*>(&dispatch), reinterpret_cast<void*>(original));
        if (result == 0) {
            installed = false;
        }
    }
    return result;
}

void dispatch(void* manager, void* view_target, float delta_time) {
    original(manager, view_target, delta_time);
    AcquireSRWLockExclusive(&guard);
    if (installed && deadline && GetTickCount64() >= deadline) {
        stop_locked();
    }
    if (stats.active && manager == target_manager) {
        ++stats.calls;
        if (apex_camera::memory_access(view_target, view_required_size, true)
            && shift_view(config, view_target, stats, !suspended)) {
            if (!suspended) {
                ++stats.writes;
            }
        } else {
            ++stats.rejected;
        }
    }
    ReleaseSRWLockExclusive(&guard);
}

int start_locked(void* manager, const Config& candidate) {
    if (installed || !valid_config(candidate) || !apex_camera::memory_access(manager, sizeof(void*))) {
        return 1;
    }
    const auto module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if (candidate.expected_rva > UINTPTR_MAX - module) {
        return 2;
    }
    auto* expected = reinterpret_cast<void*>(module + candidate.expected_rva);
    if (!apex_camera::executable_in_main_module(expected)) {
        return 2;
    }
    auto** table = *static_cast<void***>(manager);
    void** slot = table + candidate.slot_index;
    if (!apex_camera::memory_access(slot, sizeof(void*)) || *slot != expected
        || (hooked_slot && (hooked_slot != slot || reinterpret_cast<void*>(original) != expected))) {
        return 2;
    }
    HMODULE pinned_module;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                           reinterpret_cast<LPCWSTR>(&dispatch), &pinned_module)) {
        return 3;
    }
    if (!original) {
        original = reinterpret_cast<Update>(expected);
    }
    hooked_slot = slot;
    target_manager = manager;
    config = candidate;
    stats = {};
    stats.slot_index = candidate.slot_index;
    deadline = candidate.duration_ms ? GetTickCount64() + candidate.duration_ms : 0;
    suspended = false;
    if (apex_camera::replace_slot(slot, expected, reinterpret_cast<void*>(&dispatch)) != 0) {
        return 4;
    }
    installed = true;
    stats.active = 1;
    return 0;
}
}

int view_start(void* manager, const Config* candidate) {
    if (!apex_camera::memory_access(const_cast<Config*>(candidate), sizeof(Config))) {
        return 1;
    }
    AcquireSRWLockExclusive(&guard);
    const int result = start_locked(manager, *candidate);
    ReleaseSRWLockExclusive(&guard);
    return result;
}

int view_stop() {
    AcquireSRWLockExclusive(&guard);
    const int result = stop_locked();
    ReleaseSRWLockExclusive(&guard);
    return result;
}

int view_set_suspended(uint32_t value) {
    AcquireSRWLockExclusive(&guard);
    if (!installed || value > 1) {
        ReleaseSRWLockExclusive(&guard);
        return 1;
    }
    suspended = value != 0;
    stats.suspended = suspended ? 1U : 0U;
    ReleaseSRWLockExclusive(&guard);
    return 0;
}

int view_stats(Stats* output) {
    if (!apex_camera::memory_access(output, sizeof(Stats), true)) {
        return 1;
    }
    AcquireSRWLockShared(&guard);
    *output = stats;
    output->active = stats.active && (!deadline || GetTickCount64() < deadline);
    ReleaseSRWLockShared(&guard);
    return 0;
}

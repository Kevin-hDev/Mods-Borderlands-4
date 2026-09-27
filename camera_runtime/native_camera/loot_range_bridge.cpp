#include "loot_range_logic.h"
#include "loot_range_fingerprints.h"
#include "camera_memory.h"
#include <atomic>
#include <cstring>
#include <intrin.h>
#pragma intrinsic(_ReturnAddress)

namespace {
using Getter = void* (*)(void*);
SRWLOCK guard = SRWLOCK_INIT;
Getter original = nullptr;
void** slot = nullptr;
bool installed = false;
std::atomic<bool> active{false};
std::atomic<float> distance{apex_loot::min_distance};
thread_local apex_loot::OverridePool pool{};

void* dispatch(void* self) {
    const uintptr_t caller = reinterpret_cast<uintptr_t>(_ReturnAddress());
    void* result = original(self);
    if (!active.load(std::memory_order_acquire)) return result;
    const uintptr_t module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    return const_cast<void*>(apex_loot::prepare_override(caller - module, result, distance.load(), pool));
}
}

extern "C" __declspec(dllexport) int loot_start(uint32_t abi, float value) {
    if (abi != 1 || !apex_loot::valid_distance(value)) return 1;
    AcquireSRWLockExclusive(&guard);
    const uintptr_t module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    auto* expected = reinterpret_cast<void*>(module + apex_loot::pickup_getter_rva);
    auto** candidate = reinterpret_cast<void**>(module + apex_loot::pickup_slot_rva);
    int status = 0;
    if (installed) {
        status = 2;
    } else if (!apex_loot::range_fingerprints_match(module)
               || !apex_camera::memory_access(candidate, sizeof(void*)) || *candidate != expected
               || !apex_camera::executable_in_main_module(expected)) {
        status = 3;
    } else {
        HMODULE pinned{};
        if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                               reinterpret_cast<LPCWSTR>(&dispatch), &pinned)) {
            status = 4;
        } else {
            original = reinterpret_cast<Getter>(expected);
            slot = candidate;
            status = apex_camera::replace_slot(slot, expected, reinterpret_cast<void*>(&dispatch));
            if (!status) {
                installed = true;
                distance.store(value);
                active.store(true, std::memory_order_release);
            }
        }
    }
    ReleaseSRWLockExclusive(&guard);
    return status;
}

extern "C" __declspec(dllexport) int loot_distance(float value) {
    if (!apex_loot::valid_distance(value)) return 1;
    if (!active.load()) return 2;
    distance.store(value);
    return 0;
}

extern "C" __declspec(dllexport) int loot_stop() {
    active.store(false, std::memory_order_release);
    AcquireSRWLockExclusive(&guard);
    int status = 0;
    if (installed) {
        status = apex_camera::replace_slot(slot, reinterpret_cast<void*>(&dispatch),
                                           reinterpret_cast<void*>(original));
        if (!status) installed = false;
    }
    ReleaseSRWLockExclusive(&guard);
    return status;
}

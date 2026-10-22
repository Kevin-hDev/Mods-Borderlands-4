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
// Set before the slot is replaced and kept while installed, so dispatch never reads it unset.
const apex_loot::Addresses* build = nullptr;
std::atomic<bool> active{false};
std::atomic<float> distance{apex_loot::min_distance};
thread_local apex_loot::OverridePool pool{};

void* dispatch(void* self) {
    const uintptr_t caller = reinterpret_cast<uintptr_t>(_ReturnAddress());
    void* result = original(self);
    if (!active.load(std::memory_order_acquire)) return result;
    const uintptr_t module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    return const_cast<void*>(apex_loot::prepare_override(*build, caller - module, result, distance.load(), pool));
}
}

extern "C" __declspec(dllexport) int loot_start(uint32_t abi, float value) {
    if (abi != 1 || !apex_loot::valid_distance(value)) return 1;
    AcquireSRWLockExclusive(&guard);
    const uintptr_t module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    const apex_loot::Addresses* found = installed ? nullptr : apex_loot::matching_build(module);
    int status = 0;
    if (installed) {
        status = 2;
    } else if (!found) {
        status = 3;
    } else {
        auto* expected = reinterpret_cast<void*>(module + found->pickup_getter);
        auto** candidate = reinterpret_cast<void**>(module + found->pickup_slot);
        HMODULE pinned{};
        if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                               reinterpret_cast<LPCWSTR>(&dispatch), &pinned)) {
            status = 4;
        } else {
            original = reinterpret_cast<Getter>(expected);
            slot = candidate;
            build = found;
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

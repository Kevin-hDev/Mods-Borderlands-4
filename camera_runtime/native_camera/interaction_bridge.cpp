#include <cstddef>
#include "interaction_bridge.h"
#include "camera_memory.h"
#include "interaction_alignment.h"
#include "camera_builds.h"
#include <atomic>
#include <cmath>
#include <cstring>

namespace apex_interaction {
bool passive_call(Eyes original, void* self, void* location, void* rotation, void* target, View& before) {
    original(self, location, rotation);
    if (self != target || !apex_camera::memory_access(location, sizeof(before.origin))
        || !apex_camera::memory_access(rotation, sizeof(before.rotation))) return false;
    std::memcpy(before.origin, location, sizeof(before.origin));
    std::memcpy(before.rotation, rotation, sizeof(before.rotation));
    for (size_t i = 0; i < 3; ++i) {
        if (!std::isfinite(before.origin[i]) || !std::isfinite(before.rotation[i])
            || std::abs(before.origin[i]) > max_coordinate || std::abs(before.rotation[i]) > max_angle) return false;
    }
    return true;
}
}

namespace {
SRWLOCK guard = SRWLOCK_INIT;
apex_interaction::Eyes original = nullptr;
std::atomic<void*> target{nullptr};
void** hooked_slot = nullptr;
apex_interaction::Stats stats{};
apex_interaction::Config configuration{};
apex_interaction::ViewStats view_stats = nullptr;

void dispatch(void* self, void* location, void* rotation) {
    void* hunter = target.load(std::memory_order_acquire);
    if (self != hunter) {
        // Every other character (enemies ask often): the game's answer, untouched and without waiting.
        original(self, location, rotation);
        return;
    }
    apex_interaction::View before{};
    const bool valid = apex_interaction::passive_call(original, self, location, rotation, hunter, before);
    AcquireSRWLockExclusive(&guard);
    if (stats.active) {
        ++stats.calls;
        stats.tick_ms = GetTickCount64();
        if (!valid) {
            ++stats.invalid;
        } else {
            ++stats.valid;
            stats.eyes = stats.output = before;
            apex_interaction::View camera{}, aligned{};
            const int ready = apex_interaction::read_camera(configuration, view_stats, camera);
            if (ready == 1 && apex_interaction::align(before, camera, aligned)
                && apex_camera::memory_access(location, sizeof(aligned.origin), true)
                && apex_camera::memory_access(rotation, sizeof(aligned.rotation), true)) {
                std::memcpy(location, aligned.origin, sizeof(aligned.origin));
                std::memcpy(rotation, aligned.rotation, sizeof(aligned.rotation));
                stats.output = aligned;
                ++stats.writes;
            } else if (ready == 0) {
                ++stats.bypassed;
            } else {
                ++stats.rejected_view;
            }
        }
    }
    ReleaseSRWLockExclusive(&guard);
}

int start_locked(const apex_interaction::Config& config) {
    if (stats.installed || config.abi != apex_interaction::abi || config.reserved
        || config.pawn < 0x10000 || config.pawn % sizeof(void*)
        || config.controller < 0x10000 || config.controller % sizeof(void*)) return 1;
    auto* pawn = reinterpret_cast<void*>(config.pawn);
    if (!apex_camera::memory_access(pawn, sizeof(void*))) return 2;
    const uintptr_t module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    // Selects this build's addresses too (camera_builds::publish): every rva() below depends on it.
    view_stats = apex_interaction::validate_camera(config, module);
    if (!view_stats) return 7;
    // The hunter's own table: 17 tables hold this function (derived classes); only the hunter's is touched.
    auto** table = *static_cast<void***>(pawn);
    if (!apex_camera::memory_access(table, (apex_interaction::eyes_slot + 1) * sizeof(void*))) return 3;
    const uintptr_t eyes_rva = camera_builds::rva(apex_interaction::eyes_rva);
    auto* expected = reinterpret_cast<void*>(module + eyes_rva);
    void** slot = table + apex_interaction::eyes_slot;
    if (!eyes_rva || *slot != expected || !apex_camera::executable_in_main_module(expected)) return 4;
    // The same first bytes in the Steam and Epic builds of 2026-10-08.
    constexpr unsigned char head[] = {0x41, 0x57, 0x41, 0x56, 0x56, 0x57, 0x53, 0x48,
                                      0x81, 0xEC, 0xD0, 0x00, 0x00, 0x00, 0x66, 0x0F};
    if (!apex_camera::memory_access(expected, sizeof(head)) || std::memcmp(expected, head, sizeof(head))) return 5;
    HMODULE pinned{};
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                           reinterpret_cast<LPCWSTR>(&dispatch), &pinned)) return 6;
    original = reinterpret_cast<apex_interaction::Eyes>(expected);
    target.store(pawn, std::memory_order_release);
    configuration = config;
    stats = {};
    const int status = apex_camera::replace_slot(slot, expected, reinterpret_cast<void*>(&dispatch));
    if (status) {
        target.store(nullptr, std::memory_order_release);
        return 10 + status;
    }
    hooked_slot = slot;
    stats.active = stats.installed = 1;
    return 0;
}
}

int interaction_start(const apex_interaction::Config* config) {
    if (!apex_camera::memory_access(const_cast<apex_interaction::Config*>(config), sizeof(*config))) return 1;
    AcquireSRWLockExclusive(&guard);
    const int result = start_locked(*config);
    ReleaseSRWLockExclusive(&guard);
    return result;
}

int interaction_stop() {
    AcquireSRWLockExclusive(&guard);
    stats.active = 0;
    int result = 0;
    if (stats.installed) {
        result = apex_camera::replace_slot(hooked_slot, reinterpret_cast<void*>(&dispatch),
                                           reinterpret_cast<void*>(original));
        if (!result) {
            stats.installed = 0;
            // A call already inside dispatch still finds the game's function through `original`.
            target.store(nullptr, std::memory_order_release);
        }
    }
    ReleaseSRWLockExclusive(&guard);
    return result;
}

int interaction_stats(apex_interaction::Stats* output) {
    if (!apex_camera::memory_access(output, sizeof(*output), true)) return 1;
    AcquireSRWLockShared(&guard);
    *output = stats;
    ReleaseSRWLockShared(&guard);
    return 0;
}

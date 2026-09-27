#include <cstddef>
#include "interaction_bridge.h"
#include "camera_memory.h"
#include "interaction_alignment.h"
#include <atomic>
#include <cmath>
#include <cstring>

namespace apex_interaction {
bool passive_call(Provider original, void* self, void* output, void* target,
                  Sample& sample, bool& valid) {
    const bool result = original(self, output);
    valid = false;
    if (!result || self != target || !apex_camera::memory_access(output, sizeof(Sample))) {
        return result;
    }
    Sample candidate{};
    std::memcpy(&candidate, output, sizeof(candidate));
    for (size_t i = 0; i < 3; ++i) {
        if (!std::isfinite(candidate.origin[i]) || !std::isfinite(candidate.anchor[i])
            || !std::isfinite(candidate.rotation[i])
            || std::abs(candidate.origin[i]) > max_coordinate
            || std::abs(candidate.anchor[i]) > max_coordinate
            || std::abs(candidate.rotation[i]) > max_angle) return result;
    }
    sample = candidate;
    valid = true;
    return result;
}
}

namespace {
SRWLOCK guard = SRWLOCK_INIT;
apex_interaction::Provider original = nullptr;
std::atomic<void*> target{nullptr};
void** hooked_slot = nullptr;
apex_interaction::Stats stats{};
apex_interaction::Config configuration{};
apex_interaction::ViewStats view_stats = nullptr;

bool dispatch(void* self, void* output) {
    apex_interaction::Sample sample{};
    bool valid = false;
    const bool result = apex_interaction::passive_call(original, self, output, target.load(), sample, valid);
    AcquireSRWLockExclusive(&guard);
    if (stats.active) {
        ++stats.calls;
        if (self == target.load()) {
            ++stats.matches;
            stats.tick_ms = GetTickCount64();
            stats.last_success = valid ? 1U : 0U;
            if (valid) {
                stats.sample = sample;
                ++stats.valid;
                std::memcpy(stats.output_origin, sample.origin, sizeof(sample.origin));
                std::memcpy(stats.output_rotation, sample.rotation, sizeof(sample.rotation));
                if (view_stats != nullptr) {
                    apex_interaction::CameraView view{};
                    const int ready = apex_interaction::read_camera(configuration, view_stats, view);
                    if (ready == 1 && apex_interaction::align_output(output, sample, view)) {
                        ++stats.writes;
                        std::memcpy(&view, output, sizeof(view));
                        std::memcpy(stats.output_origin, view.origin, sizeof(view.origin));
                        std::memcpy(stats.output_rotation, view.rotation, sizeof(view.rotation));
                    } else if (ready == 0) {
                        ++stats.bypassed;
                    } else {
                        ++stats.rejected_view;
                    }
                }
            } else {
                ++stats.invalid;
            }
        }
    }
    ReleaseSRWLockExclusive(&guard);
    return result;
}

int start_locked(const apex_interaction::Config& config) {
    if (stats.installed || config.abi != apex_interaction::abi || config.reserved
        || config.controller < 0x10000 || config.controller % sizeof(void*)
        || config.controller > UINTPTR_MAX - apex_interaction::provider_offset) return 1;
    auto* provider = reinterpret_cast<void*>(config.controller + apex_interaction::provider_offset);
    if (!apex_camera::memory_access(provider, sizeof(void*))) return 2;
    const uintptr_t module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    auto** table = *static_cast<void***>(provider);
    if (reinterpret_cast<uintptr_t>(table) != module + apex_interaction::table_rva
        || !apex_camera::memory_access(table, (apex_interaction::provider_slot + 1) * sizeof(void*))) return 3;
    auto* expected = reinterpret_cast<void*>(module + apex_interaction::provider_rva);
    void** slot = table + apex_interaction::provider_slot;
    if (*slot != expected || !apex_camera::executable_in_main_module(expected)) return 4;
    // Match both the producer and its call into the pawn before observing this build.
    constexpr unsigned char head[] = {0x41, 0x56, 0x56, 0x57, 0x55, 0x53, 0x48, 0x83, 0xEC, 0x20};
    constexpr unsigned char call[] = {0xFF, 0x90, 0x88, 0x05, 0x00, 0x00};
    auto* call_site = reinterpret_cast<void*>(module + 0x1E49D3);
    if (!apex_camera::memory_access(expected, sizeof(head))
        || !apex_camera::memory_access(call_site, sizeof(call))
        || std::memcmp(expected, head, sizeof(head))
        || std::memcmp(call_site, call, sizeof(call))) return 5;
    view_stats = apex_interaction::validate_camera(config, module);
    if (!view_stats) return 7;
    HMODULE pinned{};
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                           reinterpret_cast<LPCWSTR>(&dispatch), &pinned)) return 6;
    if (!original) original = reinterpret_cast<apex_interaction::Provider>(expected);
    target.store(provider);
    configuration = config;
    stats = {};
    const int status = apex_camera::replace_slot(slot, expected, reinterpret_cast<void*>(&dispatch));
    if (status) return 10 + status;
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
        if (!result) stats.installed = 0;
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

#include <cstddef>
#include "beam_bridge.h"
#include "camera_memory.h"
#include "interaction_alignment.h"
#include <atomic>
#include <cmath>
#include <cstring>

namespace apex_beam {
Alignment align_query(const Query& game, const apex_interaction::View& camera, Query& aligned) {
    double ahead[3]{}, dot = 0, length = 0;
    apex_interaction::forward(camera.rotation, ahead);
    for (size_t i = 0; i < 3; ++i) {
        if (!std::isfinite(game.direction[i])) return Alignment::off_view;
        dot += game.direction[i] * ahead[i];
        length += game.direction[i] * game.direction[i];
    }
    if (!(length > 0) || dot < min_view_cosine * std::sqrt(length)) return Alignment::off_view;
    // The same move as the hunter's eyes (interaction_alignment.cpp): onto the crosshair's line, at the query's own
    // depth, so the line keeps clear of what stands between the camera and the hunter.
    const apex_interaction::View start{{game.origin[0], game.origin[1], game.origin[2]},
                                       {camera.rotation[0], camera.rotation[1], camera.rotation[2]}};
    apex_interaction::View moved{};
    if (!apex_interaction::align(start, camera, moved)) return Alignment::rejected_view;
    std::memcpy(aligned.origin, moved.origin, sizeof(aligned.origin));
    std::memcpy(aligned.direction, ahead, sizeof(aligned.direction));
    return Alignment::written;
}
}

namespace {
SRWLOCK guard = SRWLOCK_INIT;
apex_beam::Endpoint original = nullptr;
std::atomic<void*> target{nullptr};
uint32_t instigator_offset = 0;
void** hooked_slot = nullptr;
apex_beam::Stats stats{};
apex_beam::Config configuration{};
apex_interaction::ViewStats view_stats = nullptr;

void* instigator(void* beam) {
    void* who = nullptr;
    std::memcpy(&who, static_cast<unsigned char*>(beam) + instigator_offset, sizeof(who));
    return who;
}

void dispatch(void* beam, float delta) {
    void* hunter = target.load(std::memory_order_acquire);
    if (!hunter || instigator(beam) != hunter) {
        // Every other beam (enemies, other players): the game's own step, untouched and without waiting.
        original(beam, delta);
        return;
    }
    auto* fields = static_cast<unsigned char*>(beam);
    AcquireSRWLockExclusive(&guard);
    if (stats.active) {
        ++stats.calls;
        stats.tick_ms = GetTickCount64();
        apex_beam::Query game{}, aligned{};
        std::memcpy(game.origin, fields + apex_beam::origin_offset, sizeof(game.origin));
        std::memcpy(game.direction, fields + apex_beam::direction_offset, sizeof(game.direction));
        stats.before = stats.after = game;
        apex_interaction::View camera{};
        const int ready = apex_interaction::read_camera(configuration.camera, view_stats, camera);
        const auto result = ready == 1 ? apex_beam::align_query(game, camera, aligned)
                                       : apex_beam::Alignment::rejected_view;
        if (result == apex_beam::Alignment::written) {
            std::memcpy(fields + apex_beam::origin_offset, aligned.origin, sizeof(aligned.origin));
            std::memcpy(fields + apex_beam::direction_offset, aligned.direction, sizeof(aligned.direction));
            stats.after = aligned;
            ++stats.writes;
        } else if (ready == 0) {
            ++stats.bypassed;
        } else if (result == apex_beam::Alignment::off_view) {
            ++stats.off_view;
        } else {
            ++stats.rejected_view;
        }
    }
    ReleaseSRWLockExclusive(&guard);
    original(beam, delta);
}

int start_locked(const apex_beam::Config& config) {
    const auto& camera = config.camera;
    if (stats.installed || camera.abi != apex_interaction::abi || camera.reserved || config.reserved
        || camera.pawn < 0x10000 || camera.pawn % sizeof(void*)
        || camera.controller < 0x10000 || camera.controller % sizeof(void*)
        || config.beam_default < 0x10000 || config.beam_default % sizeof(void*)
        || !config.instigator_offset || config.instigator_offset > apex_beam::max_field_offset
        || config.instigator_offset % sizeof(void*)) return 1;
    auto* beam_default = reinterpret_cast<void*>(config.beam_default);
    if (!apex_camera::memory_access(beam_default, config.instigator_offset + sizeof(void*))) return 2;
    const uintptr_t module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    view_stats = apex_interaction::validate_camera(camera, module);
    if (!view_stats) return 7;
    auto** table = *static_cast<void***>(beam_default);
    if (!apex_camera::memory_access(table, (apex_beam::endpoint_slot + 1) * sizeof(void*))) return 3;
    void** slot = table + apex_beam::endpoint_slot;
    void* expected = *slot;
    // Already replaced by someone (a hook of another mod sits outside the game's module): never stacked.
    if (!apex_camera::executable_in_main_module(expected)) return 4;
    // The endpoint step's first bytes in the Steam build (0xA640F0); another function in this slot does not match.
    constexpr unsigned char head[] = {0x41, 0x57, 0x41, 0x56, 0x56, 0x57, 0x53, 0x48, 0x81, 0xEC, 0x90, 0x01,
                                      0x00, 0x00, 0x66, 0x44, 0x0F, 0x29, 0xBC, 0x24, 0x80, 0x01, 0x00, 0x00};
    if (!apex_camera::memory_access(expected, sizeof(head)) || std::memcmp(expected, head, sizeof(head))) return 5;
    HMODULE pinned{};
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                           reinterpret_cast<LPCWSTR>(&dispatch), &pinned)) return 6;
    original = reinterpret_cast<apex_beam::Endpoint>(expected);
    instigator_offset = config.instigator_offset;
    configuration = config;
    stats = {};
    target.store(reinterpret_cast<void*>(camera.pawn), std::memory_order_release);
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

int beam_start(const apex_beam::Config* config) {
    if (!apex_camera::memory_access(const_cast<apex_beam::Config*>(config), sizeof(*config))) return 1;
    AcquireSRWLockExclusive(&guard);
    const int result = start_locked(*config);
    ReleaseSRWLockExclusive(&guard);
    return result;
}

int beam_stop() {
    AcquireSRWLockExclusive(&guard);
    stats.active = 0;
    int result = 0;
    if (stats.installed) {
        result = apex_camera::replace_slot(hooked_slot, reinterpret_cast<void*>(&dispatch),
                                           reinterpret_cast<void*>(original));
        if (!result) {
            stats.installed = 0;
            // A call already inside dispatch still finds the game's step through `original`.
            target.store(nullptr, std::memory_order_release);
        }
    }
    ReleaseSRWLockExclusive(&guard);
    return result;
}

int beam_stats(apex_beam::Stats* output) {
    if (!apex_camera::memory_access(output, sizeof(*output), true)) return 1;
    AcquireSRWLockShared(&guard);
    *output = stats;
    ReleaseSRWLockShared(&guard);
    return 0;
}

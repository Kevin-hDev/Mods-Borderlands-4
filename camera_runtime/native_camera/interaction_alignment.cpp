#include "interaction_alignment.h"
#include "camera_memory.h"
#include <cmath>
#include <cstring>

namespace apex_interaction {
bool align_output(void* output, const Sample& before, const CameraView& view) {
    if (!apex_camera::memory_access(output, sizeof(view), true)) return false;
    double distance_squared = 0;
    for (size_t i = 0; i < 3; ++i) {
        if (!std::isfinite(view.origin[i]) || !std::isfinite(view.rotation[i])
            || !std::isfinite(before.origin[i]) || std::abs(view.origin[i]) > max_coordinate
            || std::abs(view.rotation[i]) > max_angle) return false;
        const double delta = view.origin[i] - before.origin[i];
        distance_squared += delta * delta;
    }
    if (distance_squared > max_camera_distance * max_camera_distance) return false;
    const double pitch = view.rotation[0] * radians_per_degree;
    const double yaw = view.rotation[1] * radians_per_degree;
    const double forward[] = {std::cos(pitch) * std::cos(yaw),
                              std::cos(pitch) * std::sin(yaw), std::sin(pitch)};
    double depth = 0;
    for (size_t i = 0; i < 3; ++i) depth += (before.origin[i] - view.origin[i]) * forward[i];
    if (depth < 0) return false;
    CameraView aligned = view;
    // Project onto the camera ray at the original depth: moving back to the camera
    // itself would spend the finite interaction segment on the camera boom.
    for (size_t i = 0; i < 3; ++i) aligned.origin[i] += depth * forward[i];
    // Only the ray changes: the original anchor, range and ignored actors remain authoritative.
    std::memcpy(output, &aligned, sizeof(aligned));
    return true;
}

int read_camera(const Config& config, ViewStats getter, CameraView& view) {
    apex_view::Stats camera{};
    if (!getter || getter(&camera)) return -1;
    if (!camera.active || camera.suspended) return 0;
    auto* pc = reinterpret_cast<unsigned char*>(config.controller);
    auto* manager = reinterpret_cast<unsigned char*>(config.manager);
    if (!apex_camera::memory_access(pc, manager_offset + sizeof(void*))) return -1;
    uint64_t pawn_now{}, manager_now{};
    std::memcpy(&pawn_now, pc + pawn_offset, sizeof(pawn_now));
    std::memcpy(&manager_now, pc + manager_offset, sizeof(manager_now));
    if (pawn_now != config.pawn || manager_now != config.manager) return 0;
    if (!apex_camera::memory_access(manager, cache_view_offset + sizeof(view))) return -1;
    float timestamp{};
    std::memcpy(&timestamp, manager + cache_time_offset, sizeof(timestamp));
    if (!std::isfinite(timestamp) || timestamp <= 0) return -1;
    // These are the same cached fields read by the game's GetPlayerViewPoint implementation.
    std::memcpy(&view, manager + cache_view_offset, sizeof(view));
    return 1;
}

ViewStats validate_camera(const Config& config, uintptr_t module) {
    if (!config.pawn || !config.manager || !config.camera_module) return nullptr;
    auto* address = reinterpret_cast<void*>(module + 0x48814D9);
    constexpr unsigned char cache_read[] = {0x48, 0x81, 0xC7, 0x10, 0x19, 0x00, 0x00};
    if (!apex_camera::memory_access(address, sizeof(cache_read))
        || std::memcmp(address, cache_read, sizeof(cache_read))) return nullptr;
    // Resolve an existing native export; no Python callback is installed in the game thread.
    const auto symbol = GetProcAddress(reinterpret_cast<HMODULE>(config.camera_module), "view_stats");
    if (!symbol) return nullptr;
    HMODULE pinned{};
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                           reinterpret_cast<LPCWSTR>(symbol), &pinned)
        || reinterpret_cast<uintptr_t>(pinned) != config.camera_module) return nullptr;
    ViewStats getter{};
    static_assert(sizeof(getter) == sizeof(symbol));
    std::memcpy(&getter, &symbol, sizeof(getter));
    // A new map may not have its first cached view yet; callbacks stay read-only until it does.
    return getter;
}
}

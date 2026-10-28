#include "view_state.h"
#include "camera_memory.h"
#include "ads_api.h"
#include <cmath>

using namespace apex_view;
using namespace apex_view::detail;

namespace apex_view::detail {
SRWLOCK guard = SRWLOCK_INIT;
Update original = nullptr;
void** hooked_slot = nullptr;
void* target_manager = nullptr;
Config config{};
Stats stats{};
ULONGLONG deadline = 0;
bool installed = false, suspended = false;
apex_ads::FramingContext framing{};
apex_framing::Status framing_status = apex_framing::Status::disabled;
bool framing_zoom_pending = false;
CollisionResolver collision = nullptr;
DWORD owner_thread = 0;
uint64_t generation = 0;

int stop_locked() {
    ++generation;
    stats.active = 0;
    offset_blend.reset();
    offset_smoothing = false;
    shoulder_blending = false;
    framing = {};
    framing_status = apex_framing::Status::disabled;
    framing_zoom_pending = false;
    int result = 0;
    if (installed) {
        result = apex_camera::replace_slot(
            hooked_slot, reinterpret_cast<void*>(&dispatch), reinterpret_cast<void*>(original));
        if (result == 0) installed = false;
    }
    // Python retains its thunk on a refused stop; do not lose the native reference early.
    if (!installed) collision = nullptr;
    return result;
}
}

namespace {
int start_locked(void* manager, const Config& candidate) {
    if (installed || !valid_config(candidate) || !apex_camera::memory_access(manager, sizeof(void*))) return 1;
    const auto module = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if (candidate.expected_rva > UINTPTR_MAX - module) return 2;
    auto* expected = reinterpret_cast<void*>(module + candidate.expected_rva);
    if (!apex_camera::executable_in_main_module(expected)) return 2;
    auto** table = *static_cast<void***>(manager);
    void** slot = table + candidate.slot_index;
    if (!apex_camera::memory_access(slot, sizeof(void*)) || *slot != expected
        || (hooked_slot && (hooked_slot != slot || reinterpret_cast<void*>(original) != expected))) return 2;
    HMODULE pinned_module;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                           reinterpret_cast<LPCWSTR>(&dispatch), &pinned_module)) return 3;
    if (!original) original = reinterpret_cast<Update>(expected);
    hooked_slot = slot;
    target_manager = manager;
    config = candidate;
    stats = {};
    framing = {};
    framing_status = apex_framing::Status::disabled;
    framing_zoom_pending = false;
    collision = nullptr;
    owner_thread = GetCurrentThreadId();
    ++generation;
    stats.slot_index = candidate.slot_index;
    deadline = candidate.duration_ms ? GetTickCount64() + candidate.duration_ms : 0;
    suspended = false;
    offset_blend.reset();
    shoulder_seconds = 0;
    offset_smoothing = false;
    shoulder_blending = false;
    if (apex_camera::replace_slot(slot, expected, reinterpret_cast<void*>(&dispatch)) != 0) return 4;
    installed = true;
    stats.active = 1;
    return 0;
}
}

int view_start(void* manager, const Config* candidate) {
    if (!apex_camera::memory_access(const_cast<Config*>(candidate), sizeof(Config))) return 1;
    AcquireSRWLockExclusive(&guard);
    const int result = start_locked(manager, *candidate);
    ReleaseSRWLockExclusive(&guard);
    return result;
}

int view_stop() {
    AcquireSRWLockExclusive(&guard);
    if (installed && GetCurrentThreadId() != owner_thread) {
        ReleaseSRWLockExclusive(&guard);
        return 1;
    }
    // Check ownership and stop in one transaction: a new start cannot slip between them.
    const int result = stop_locked();
    stats.ads_effective = 0;
    ReleaseSRWLockExclusive(&guard);
    auto& ads = apex_ads::shared_ads();
    const auto ads_generation = ads.statistics().generation;
    if (ads_generation) ads.clear(ads_generation);
    return result;
}

int view_set_collision(CollisionResolver resolver) {
    MEMORY_BASIC_INFORMATION memory{};
    const auto pointer = reinterpret_cast<void*>(resolver);
    if (!pointer || VirtualQuery(pointer, &memory, sizeof(memory)) != sizeof(memory)
        || memory.State != MEM_COMMIT || (memory.Protect & (PAGE_GUARD | PAGE_NOACCESS))
        || !(memory.Protect & (PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY))) return 1;
    AcquireSRWLockExclusive(&guard);
    const bool accepted = installed && stats.active && GetCurrentThreadId() == owner_thread && resolver;
    if (accepted) { collision = resolver; ++generation; }
    ReleaseSRWLockExclusive(&guard);
    return accepted ? 0 : 1;
}

int view_set_suspended(uint32_t value) {
    AcquireSRWLockExclusive(&guard);
    if (!installed || value > 1) {
        ReleaseSRWLockExclusive(&guard);
        return 1;
    }
    suspended = value != 0;
    // Strong camera authorities (vehicle/native aiming) cancel interpolation immediately.
    offset_blend.reset();
    offset_smoothing = false;
    shoulder_blending = false;
    stats.suspended = suspended ? 1U : 0U;
    ++generation;
    ReleaseSRWLockExclusive(&guard);
    return 0;
}

bool view_set_right(double right) {
    AcquireSRWLockExclusive(&guard);
    if (!installed || !std::isfinite(right) || std::abs(right) > max_offset) {
        ReleaseSRWLockExclusive(&guard);
        return false;
    }
    if (config.right != right) {
        offset_blend.begin(suspended ? 0 : shoulder_seconds);
        shoulder_blending = !suspended;
    }
    config.right = right;
    ++generation;
    ReleaseSRWLockExclusive(&guard);
    return true;
}

int view_stats(Stats* output) {
    if (!apex_camera::memory_access(output, sizeof(Stats), true)) return 1;
    AcquireSRWLockShared(&guard);
    *output = stats;
    output->active = stats.active && (!deadline || GetTickCount64() < deadline);
    ReleaseSRWLockShared(&guard);
    return 0;
}

int view_set_framing(const apex_ads::FramingContext* input) {
    apex_ads::FramingContext candidate{};
    bool accepted = !input;
    if (input && apex_camera::memory_access(const_cast<apex_ads::FramingContext*>(input), sizeof(*input))) {
        candidate = *input;
        accepted = apex_framing::valid(candidate);
    }
    AcquireSRWLockExclusive(&guard);
    framing = accepted && installed ? candidate : apex_ads::FramingContext{};
    framing_status = apex_framing::Status::disabled;
    framing_zoom_pending = false;
    ++generation;
    ReleaseSRWLockExclusive(&guard);
    return accepted ? 0 : 1;
}

uint32_t view_framing_status() {
    AcquireSRWLockShared(&guard);
    const auto result = framing_status;
    ReleaseSRWLockShared(&guard);
    return static_cast<uint32_t>(result);
}

bool view_framing_zoom_pending() {
    AcquireSRWLockShared(&guard);
    const bool result = stats.active && framing_zoom_pending;
    ReleaseSRWLockShared(&guard);
    return result;
}

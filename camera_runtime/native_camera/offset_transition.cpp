#include "view_state.h"
#include "generated_transition_limits.h"
#include <cmath>

namespace apex_view::detail {
OffsetBlend offset_blend{};
double shoulder_seconds = 0;
bool offset_smoothing = false;
bool shoulder_blending = false;
}

int view_set_transition_duration(double seconds) {
    using namespace apex_view::detail;
    if (!std::isfinite(seconds) || seconds < 0 || seconds > apex_transition::shoulder_seconds_max) return 1;
    AcquireSRWLockExclusive(&guard);
    const bool accepted = installed && stats.active && GetCurrentThreadId() == owner_thread;
    if (accepted && shoulder_seconds != seconds) {
        shoulder_seconds = seconds;
        if (!seconds && shoulder_blending) offset_blend.begin(0);
        ++generation;
    }
    ReleaseSRWLockExclusive(&guard);
    return accepted ? 0 : 1;
}

int view_set_offset_suspended(uint32_t value, double seconds) {
    using namespace apex_view::detail;
    if (value > 1 || !std::isfinite(seconds) || seconds < 0
        || seconds > apex_transition::shoulder_seconds_max) return 1;
    AcquireSRWLockExclusive(&guard);
    const bool accepted = installed && stats.active && GetCurrentThreadId() == owner_thread;
    if (accepted && suspended != (value != 0)) {
        suspended = value != 0;
        stats.suspended = value;
        offset_smoothing = suspended && seconds > 0;
        shoulder_blending = false;
        offset_blend.begin(seconds);
        ++generation;
    }
    ReleaseSRWLockExclusive(&guard);
    return accepted ? 0 : 1;
}

int view_set_climb_suspended(uint32_t value) {
    // Native climbing retains its measured timing, independent of player settings.
    return view_set_offset_suspended(value, apex_transition::climb_seconds);
}

bool view_offset_transition_active() {
    using namespace apex_view::detail;
    AcquireSRWLockShared(&guard);
    const bool active = installed && stats.active && !shoulder_blending && offset_blend.active();
    ReleaseSRWLockShared(&guard);
    return active;
}

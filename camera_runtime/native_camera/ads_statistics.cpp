#include "ads_state.h"
#include "ads_memory.h"

namespace apex_ads {
void State::note_error(uint32_t error) {
    AcquireSRWLockExclusive(&guard_);
    stats_.error = error;
    stats_.active = 0;
    if (error == ERROR_WRONG_THREAD) increment(stats_.wrong_thread);
    if (error == ERROR_MODE) increment(stats_.wrong_mode);
    if (error == ERROR_IDENTITY) {
        increment(stats_.identity_refused);
    }
    if (error == ERROR_IDENTITY || error == ERROR_CONTEXT) {
        context_.enabled = 0;
        reticle_enabled_ = false;
        stats_.pending = touched_ ? 1U : 0U;
    }
    ReleaseSRWLockExclusive(&guard_);
}

void State::record_fov(const Ticket& ticket, float before, float after, float scale) {
    AcquireSRWLockExclusive(&guard_);
    if (context_.enabled && context_.generation == ticket.context.generation) {
        increment(stats_.fov_writes);
        stats_.fov_before = before; stats_.fov_after = after; stats_.zoom_scale = scale;
        stats_.active = 1;
        stats_.error = 0;
    }
    ReleaseSRWLockExclusive(&guard_);
}

void State::record_reticle(const Ticket& ticket) {
    AcquireSRWLockExclusive(&guard_);
    if (context_.enabled && reticle_enabled_ && context_.generation == ticket.context.generation) {
        increment(stats_.reticle_writes);
        touched_ = true;
    }
    ReleaseSRWLockExclusive(&guard_);
}

void State::producer_called() {
    AcquireSRWLockExclusive(&guard_);
    increment(stats_.producer_calls);
    ReleaseSRWLockExclusive(&guard_);
}
void State::getter_called() {
    AcquireSRWLockExclusive(&guard_);
    increment(stats_.getter_calls);
    ReleaseSRWLockExclusive(&guard_);
}
void State::installation_attempted() {
    AcquireSRWLockExclusive(&guard_);
    increment(stats_.install_attempts);
    ReleaseSRWLockExclusive(&guard_);
}

void State::restored(void* collector) {
    AcquireSRWLockShared(&guard_);
    const bool pending = stats_.pending && !reticle_enabled_;
    const bool thread = thread_ && thread_ == GetCurrentThreadId();
    const auto context = context_;
    const auto table = table_;
    ReleaseSRWLockShared(&guard_);
    if (!pending) return;
    if (!thread) { note_error(static_cast<uint32_t>(ERROR_WRONG_THREAD)); return; }
    uintptr_t actor{};
    if (reinterpret_cast<uintptr_t>(collector) != context.references[5].address
            || !owner_alive(table, context)
            || !read_memory(reinterpret_cast<uintptr_t>(collector), OBJECT_OUTER_OFFSET, actor)
            || actor != context.references[1].address) return;
    AcquireSRWLockExclusive(&guard_);
    if (context_.generation == context.generation && !reticle_enabled_ && stats_.pending) {
        touched_ = false;
        stats_.pending = 0;
        increment(stats_.restorations);
    }
    ReleaseSRWLockExclusive(&guard_);
}
}

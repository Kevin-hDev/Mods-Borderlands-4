#include "ads_state.h"
#include "ads_memory.h"
#include <cmath>

namespace apex_ads {
bool State::configure(uintptr_t table, uint64_t third_name, ZoomScale zoom) {
    AcquireSRWLockExclusive(&guard_);
    const bool ready = table && third_name && zoom && !thread_;
    if (ready) {
        table_ = table; third_name_ = third_name; zoom_ = zoom;
        thread_ = GetCurrentThreadId();
    }
    ReleaseSRWLockExclusive(&guard_);
    return ready;
}

void State::set_installed(bool value) {
    AcquireSRWLockExclusive(&guard_);
    stats_.installed = value ? 1U : 0U;
    ReleaseSRWLockExclusive(&guard_);
}

int State::publish(const AdsContext& candidate) {
    // Thread permission precedes every object read, including publication.
    AcquireSRWLockShared(&guard_);
    const bool thread = thread_ && thread_ == GetCurrentThreadId();
    const auto table = table_;
    ReleaseSRWLockShared(&guard_);
    const auto validation = thread ? context_error(table, candidate) : static_cast<uint32_t>(ERROR_WRONG_THREAD);
    const bool valid = validation == 0;
    AcquireSRWLockExclusive(&guard_);
    context_.enabled = 0;
    reticle_enabled_ = false;
    stats_.active = 0;
    stats_.pending = touched_ ? 1U : 0U;
    const bool accepted = valid && stats_.installed && !stats_.pending
        && candidate.generation > last_generation_;
    if (accepted) {
        context_ = candidate;
        reticle_enabled_ = true;
        last_generation_ = candidate.generation;
        stats_.generation = candidate.generation;
        stats_.active = 1;
        stats_.error = 0;
    } else {
        stats_.error = valid ? static_cast<uint32_t>(ERROR_CONTEXT) : validation;
    }
    ReleaseSRWLockExclusive(&guard_);
    return accepted ? 0 : 1;
}

int State::publish_pointer(const AdsContext* input) {
    AcquireSRWLockShared(&guard_);
    const bool thread = thread_ && thread_ == GetCurrentThreadId();
    const auto generation = context_.generation;
    ReleaseSRWLockShared(&guard_);
    AdsContext candidate{};
    if (!thread || !read_memory(reinterpret_cast<uintptr_t>(input), 0, candidate)) {
        clear(generation);
        note_error(static_cast<uint32_t>(thread ? ERROR_CONTEXT : ERROR_WRONG_THREAD));
        return 1;
    }
    return publish(candidate);
}

int State::set_optic(uint64_t generation, float scale) {
    AcquireSRWLockExclusive(&guard_);
    const bool thread = thread_ && thread_ == GetCurrentThreadId();
    // 0 gives the weapon's own zoom back, 1 no zoom; an optic never widens the view.
    const bool valid = std::isfinite(scale) && scale >= 0.0f && scale <= 1.0f;
    const bool accepted = thread && valid && generation && context_.enabled && generation == context_.generation;
    if (accepted) {
        optic_generation_ = generation;
        optic_ = scale;
    }
    ReleaseSRWLockExclusive(&guard_);
    if (!thread) note_error(static_cast<uint32_t>(ERROR_WRONG_THREAD));
    return accepted ? 0 : 1;
}

float State::optic(const Ticket& ticket) {
    AcquireSRWLockShared(&guard_);
    const float value = optic_generation_ == ticket.context.generation ? optic_ : 0.0f;
    ReleaseSRWLockShared(&guard_);
    return value;
}

int State::clear(uint64_t generation) {
    AcquireSRWLockExclusive(&guard_);
    context_.enabled = 0;
    reticle_enabled_ = false;
    stats_.active = 0;
    stats_.pending = touched_ ? 1U : 0U;
    const bool same = generation == context_.generation;
    // Expose this cleanup's outcome, not a stale refusal from a preceding frame.
    stats_.error = 0;
    const bool may_read = thread_ && thread_ == GetCurrentThreadId();
    const auto context = context_;
    const auto table = table_;
    ReleaseSRWLockExclusive(&guard_);
    const auto ownership = may_read ? owner_error(table, context) : 0U;
    if (ownership) {
        AcquireSRWLockExclusive(&guard_);
        if (context_.generation == context.generation && !context_.enabled) {
            stats_.pending = 0;
            touched_ = false;
            stats_.error = ownership;
        }
        ReleaseSRWLockExclusive(&guard_);
    }
    return same ? 0 : 1;
}

int State::release(uint64_t generation) {
    AcquireSRWLockExclusive(&guard_);
    const bool thread = thread_ && thread_ == GetCurrentThreadId();
    const bool accepted = thread && generation && context_.enabled && stats_.installed
        && generation == context_.generation;
    // Revoke HUD adaptation immediately, but keep the guarded view ticket for native zoom-out.
    reticle_enabled_ = false;
    stats_.pending = touched_ ? 1U : 0U;
    if (!accepted) context_.enabled = 0;
    ReleaseSRWLockExclusive(&guard_);
    if (!accepted) note_error(static_cast<uint32_t>(thread ? ERROR_CONTEXT : ERROR_WRONG_THREAD));
    return accepted ? 0 : 1;
}

bool State::reticle_current(const Ticket& previous) {
    if (!current(previous)) return false;
    AcquireSRWLockShared(&guard_);
    const bool allowed = reticle_enabled_ && context_.enabled
        && context_.generation == previous.context.generation;
    ReleaseSRWLockShared(&guard_);
    return allowed;
}

bool State::reticle_ticket(Ticket& output) {
    AcquireSRWLockShared(&guard_);
    const bool enabled = reticle_enabled_;
    ReleaseSRWLockShared(&guard_);
    return enabled && ticket(output) && reticle_current(output);
}

bool State::ticket(void* manager, Ticket& output) {
    output = {};
    AcquireSRWLockShared(&guard_);
    const bool active = context_.enabled && stats_.installed;
    const bool thread = thread_ && thread_ == GetCurrentThreadId();
    Ticket candidate{context_, {}, table_, third_name_, zoom_};
    ReleaseSRWLockShared(&guard_);
    if (!active) return false;
    if (!thread) { note_error(static_cast<uint32_t>(ERROR_WRONG_THREAD)); return false; }
    if (reinterpret_cast<uintptr_t>(manager) != candidate.context.references[2].address) {
        note_error(static_cast<uint32_t>(ERROR_CONTEXT)); return false;
    }
    const auto validation = context_error(candidate.table, candidate.context);
    if (validation) { note_error(validation); return false; }
    if (!read_mode(manager, candidate.third_name, candidate.mode)) {
        note_error(static_cast<uint32_t>(ERROR_MODE)); return false;
    }
    AcquireSRWLockShared(&guard_);
    const bool same = context_.enabled && context_.generation == candidate.context.generation;
    ReleaseSRWLockShared(&guard_);
    if (same) output = candidate;
    return same;
}

bool State::current(const Ticket& previous) {
    Ticket next{};
    return ticket(reinterpret_cast<void*>(previous.context.references[2].address), next)
        && next.context.generation == previous.context.generation
        && next.mode.object == previous.mode.object && next.mode.name == previous.mode.name;
}

bool State::ticket(Ticket& output) {
    AcquireSRWLockShared(&guard_);
    const auto manager = context_.references[2].address;
    ReleaseSRWLockShared(&guard_);
    return ticket(reinterpret_cast<void*>(manager), output);
}

AdsStats State::statistics() {
    AcquireSRWLockShared(&guard_);
    const auto result = stats_;
    ReleaseSRWLockShared(&guard_);
    return result;
}
}

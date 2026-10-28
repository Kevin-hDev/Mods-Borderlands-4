#include "ads_reticle.h"

namespace apex_ads {
thread_local Reticle::Frame* Reticle::frame_ = nullptr;

bool Reticle::configure(Producer producer, Getter getter, uintptr_t caller) {
    if (!producer || !getter || !caller || producer_ || getter_) return false;
    producer_ = producer; getter_ = getter; caller_ = caller;
    return true;
}

void Reticle::producer(void* collector, void* weapon) {
    state_.producer_called();
    Frame frame{};
    frame.owner = this; frame.collector = collector; frame.weapon = weapon;
    Frame* previous = frame_;
    frame.eligible = !previous && state_.reticle_ticket(frame.ticket)
        && frame.ticket.context.references[5].address == reinterpret_cast<uintptr_t>(collector)
        && frame.ticket.context.references[3].address == reinterpret_cast<uintptr_t>(weapon);
    frame_ = &frame;
    // Keep game exceptions intact, while restoring TLS even on native unwinding.
    __try {
        producer_(collector, weapon);
    } __finally {
        frame_ = previous;
    }
    if (!previous) state_.restored(collector);
}

bool Reticle::getter(void* weapon, uintptr_t caller) {
    state_.getter_called();
    const auto* frame = frame_;
    const bool requested = getter_(weapon);
    if (requested || !frame || frame_ != frame || frame->owner != this || !frame->eligible
            || frame->weapon != weapon || caller != caller_ || !state_.reticle_current(frame->ticket)) return requested;
    state_.record_reticle(frame->ticket);
    return true;
}
}

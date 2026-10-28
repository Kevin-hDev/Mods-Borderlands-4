#include "framing_view.h"
#include "framing_body.h"
#include "generated_framing_limits.h"
#include "ads_identity.h"
#include "ads_memory.h"
#include "interaction_alignment.h"

namespace apex_framing {
bool valid(const apex_ads::FramingContext& c) {
    using namespace apex_framing_limits;
    return c.abi == apex_ads::VIEW_ABI && c.size == sizeof(c) && !c.reserved
        && c.values[0] >= zoom_minimum && c.values[0] <= zoom_maximum
        && c.values[1] >= horizontal_minimum && c.values[1] <= horizontal_maximum
        && c.values[2] >= height_minimum && c.values[2] <= height_maximum
        && within(c.actor_size, c.root_offset, sizeof(uintptr_t))
        && within(c.actor_size, c.capsule_offset, sizeof(uintptr_t))
        && within(c.root_size, c.location_offset, 3 * sizeof(double))
        && within(c.root_size, c.parent_offset, sizeof(uintptr_t))
        && within(c.root_size, apex_ads::OBJECT_OUTER_OFFSET, sizeof(uintptr_t));
}
}
namespace apex_ads {
bool State::framing_allowed(const FramingContext& context, void* manager) {
    AcquireSRWLockShared(&guard_);
    const bool thread = thread_ && thread_ == GetCurrentThreadId();
    const uintptr_t table = table_;
    const uint64_t third = third_name_;
    ReleaseSRWLockShared(&guard_);
    if (!thread || !apex_framing::valid(context)
        || context.references[2].address != reinterpret_cast<uintptr_t>(manager)) return false;
    uintptr_t resolved{}, value{};
    for (const auto& id : context.references) if (!resolve_id(table, id, resolved)) return false;
    ModeSnapshot mode{};
    return read_memory(context.references[0].address, apex_interaction::pawn_offset, value)
        && value == context.references[1].address
        && read_memory(context.references[0].address, CONTROLLER_MANAGER_OFFSET, value)
        && value == context.references[2].address
        && read_framing_mode(manager, third, mode);
}
}

#include "anchor_pose.h"
#include "camera_memory.h"
#include "generated_ads.h"
#include <cmath>
#include <cstring>

namespace climb_anchor {
bool apply_socket(Update socket, void* context, void* state, float delta, uint64_t socket_name) {
    if (!socket || !socket_name || !std::isfinite(delta) || delta < 0
        || !apex_camera::memory_access(state, state_bytes, true)) return false;
    alignas(16) unsigned char preview[state_bytes]{};
    alignas(16) unsigned char behavior[behavior_bytes]{};
    std::memcpy(preview, state, sizeof(preview));
    // ThirdPerson has no default socket: use the explicitly qualified animated bone.
    behavior[flags_offset] = 1;
    std::memcpy(behavior + behavior_socket_offset, &socket_name, sizeof(socket_name));
    __try { socket(behavior, context, preview, delta); }
    __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    double previous[3]{}, next[3]{};
    std::memcpy(previous, static_cast<unsigned char*>(state) + position_offset, sizeof(previous));
    std::memcpy(next, preview + position_offset, sizeof(next));
    double distance_squared = 0;
    for (size_t i = 0; i < 3; ++i) {
        if (!std::isfinite(previous[i]) || !std::isfinite(next[i])
            || std::abs(next[i]) > apex_ads::CAMERA_MAX_COORDINATE) return false;
        const double difference = next[i] - previous[i];
        distance_squared += difference * difference;
    }
    if (distance_squared > max_adjustment * max_adjustment) return false;
    std::memcpy(static_cast<unsigned char*>(state) + position_offset, next, sizeof(next));
    return true;
}
}

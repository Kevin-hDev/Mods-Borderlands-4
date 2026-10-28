#pragma once
#include "camera_memory.h"
#include <array>

namespace apex_framing {
// Only code in the non-unloadable main executable is retained, never a game object.
// Live vtable slots are still read on every call; changed methods are requalified.
class ExecutableCache {
    static constexpr size_t capacity = 8;
    std::array<void*, capacity> addresses_{};
    size_t next_{};
public:
    bool accepts(void* address) {
        if (!address) return false;
        for (auto* known : addresses_) if (known == address) return true;
        if (!apex_camera::executable_in_main_module(address)) return false;
        addresses_[next_] = address;
        next_ = (next_ + 1) % capacity;
        return true;
    }
};
}

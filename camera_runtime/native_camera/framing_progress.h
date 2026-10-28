#pragma once
#include <cmath>

namespace apex_framing {
using Find = void* (*)(void*, void*);
using Cast = void* (*)(void*, void*);
using Progress = float (*)(void*);
inline bool read_progress(void* target, void* actor, void* type,
                          Find find, Cast cast, Progress progress, float& output) {
    if (!target || target != actor || !type || !find || !cast || !progress) return false;
    void* object = find(target, type);
    if (!object) return false;
    void* interface_value = cast(object, type);
    if (!interface_value || interface_value == object) return false;
    const float value = progress(interface_value);
    if (!std::isfinite(value) || value < 0 || value > 1) return false;
    output = value;
    return true;
}
}

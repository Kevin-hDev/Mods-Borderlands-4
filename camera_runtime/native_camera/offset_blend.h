#pragma once
#include <cmath>
#include <cstring>

namespace apex_view {
// Blend only our correction in the camera's yaw frame; native movement and zoom keep their own timing.
class OffsetBlend {
    double current[3]{}, start[3]{};
    double elapsed = 0, duration = 0;
    static constexpr double radians = 0.017453292519943295;
public:
    bool active() const { return duration > 0 && elapsed < duration; }
    void reset() { *this = {}; }
    void begin(double seconds) {
        std::memcpy(start, current, sizeof(start));
        elapsed = 0;
        duration = seconds;
    }
    void commit(const double* correction, double yaw) {
        const double c = std::cos(yaw * radians), s = std::sin(yaw * radians);
        current[0] = correction[0] * c + correction[1] * s;
        current[1] = -correction[0] * s + correction[1] * c;
        current[2] = correction[2];
    }
    void apply(const double* target, double yaw, double delta, double* output) {
        if (!std::isfinite(delta) || delta < 0) duration = 0;
        if (!active()) { std::memcpy(output, target, sizeof(current)); return; }
        elapsed = std::fmin(duration, elapsed + delta);
        if (duration - elapsed < 1e-9) elapsed = duration;
        const double fraction = elapsed / duration;
        const double alpha = fraction * fraction * (3 - 2 * fraction);
        const double c = std::cos(yaw * radians), s = std::sin(yaw * radians);
        const double origin[3]{start[0] * c - start[1] * s,
                               start[0] * s + start[1] * c, start[2]};
        for (size_t i = 0; i < 3; ++i) output[i] = origin[i] + (target[i] - origin[i]) * alpha;
    }
};
}

#include "framing_math.h"
#include <cmath>
#include <limits>

namespace {
// The native factor is float: do not normalize a denominator below its precision.
constexpr double precision = 8 * std::numeric_limits<float>::epsilon();

bool finite(apex_framing::Vec3 value) {
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

double dot(apex_framing::Vec3 a, apex_framing::Vec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

struct Basis { apex_framing::Vec3 right, up, forward; };

bool basis(apex_framing::Vec3 angles, Basis& output) {
    if (!finite(angles)) return false;
    const double radians = std::acos(-1.0) / 180;
    const double p = angles.x * radians, y = angles.y * radians, r = angles.z * radians;
    const double sp = std::sin(p), cp = std::cos(p), sy = std::sin(y), cy = std::cos(y);
    const double sr = std::sin(r), cr = std::cos(r);
    const Basis result{{sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp},
                       {-cr * sp * cy - sr * sy, -cr * sp * sy + sr * cy, cr * cp},
                       {cp * cy, cp * sy, sp}};
    if (!finite(result.right) || !finite(result.up) || !finite(result.forward)) return false;
    output = result;
    return true;
}
}

namespace apex_framing {
bool correct(Vec3 historical, Vec3 anchor, Vec3 angles,
             double horizontal, double vertical, Result& output) {
    Basis axes{};
    if (!finite(historical) || !finite(anchor) || !basis(angles, axes)
            || !std::isfinite(horizontal) || horizontal < 0
            || !std::isfinite(vertical)) return false;
    const Vec3 relative{anchor.x - historical.x, anchor.y - historical.y,
                        anchor.z - historical.z};
    if (!finite(relative)) return false;
    const double x = dot(relative, axes.right);
    const double z = dot(relative, axes.forward);
    if (!std::isfinite(x) || !std::isfinite(z)
            || z <= precision || std::abs(x) <= precision) return false;
    // Framing must not depend on zoom: translating the camera during ADS moves
    // its central aim ray. Let FOV magnify the character's framing naturally.
    const double right = -x * horizontal;
    const double up = vertical * std::abs(x);
    if (!std::isfinite(right) || !std::isfinite(up)) return false;
    const Vec3 corrected{historical.x + axes.right.x * right + axes.up.x * up,
                         historical.y + axes.right.y * right + axes.up.y * up,
                         historical.z + axes.right.z * right + axes.up.z * up};
    if (!finite(corrected)) return false;
    // No output can be observed until all three coordinates have passed validation.
    output = {corrected};
    return true;
}
}

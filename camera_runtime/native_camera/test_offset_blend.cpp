#include "offset_blend.h"
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>

#define check(condition) do { if (!(condition)) { \
    std::cerr << "RESULTAT: ECHEC line=" << __LINE__ << '\n'; std::exit(1); \
} } while (false)

bool near(double a, double b) { return std::abs(a - b) < 0.00001; }

int main() {
    for (int fps : {30, 60, 144}) {
        apex_view::OffsetBlend blend;
        const double initial[3]{0, 40, 5};
        blend.commit(initial, 0);
        blend.begin(0.5);
        const double target[3]{0, -40, 5};
        double output[3]{};
        for (int frame = 0; frame < fps / 2; ++frame) {
            blend.apply(target, 0, 1.0 / fps, output);
            blend.commit(output, 0);
            check(output[1] <= 40 && output[1] >= -40);
        }
        check(near(output[1], -40));
        check(!blend.active());
    }
    apex_view::OffsetBlend blend;
    const double right[3]{0, 40, 5}, left[3]{0, -40, 5}, center[3]{};
    blend.commit(right, 0);
    blend.begin(1);
    double output[3]{};
    blend.apply(left, 0, 0.5, output);
    check(near(output[1], 0));
    blend.commit(output, 0);
    blend.begin(1);
    blend.apply(right, 0, 0, output);
    check(near(output[1], 0)); // A repeated press starts at the actual rendered position.
    blend.apply(right, 0, 0.5, output);
    check(near(output[1], 20));
    blend.commit(output, 0);
    blend.begin(0.5);
    blend.apply(center, 90, 0, output);
    check(near(output[0], -20) && near(output[1], 0)); // Follow yaw, never a frozen world point.
    blend.apply(center, 90, 0.5, output);
    check(near(output[0], 0) && near(output[2], 0));
    blend.commit(left, 0);
    blend.begin(0);
    blend.apply(right, 0, 0, output);
    check(near(output[1], 40));
    blend.begin(1);
    blend.apply(left, 0, std::numeric_limits<double>::quiet_NaN(), output);
    check(!blend.active() && near(output[1], -40)); // Malformed timing cancels, not extrapolates.
    blend.commit(left, 0);
    blend.begin(1);
    blend.reset();
    blend.apply(right, 0, 0, output);
    check(near(output[1], 40)); // New owners cannot inherit an old camera animation.
    std::cout << "RESULTAT: OK - timed local camera offsets\n";
}

#include "ads_test_assert.h"
#include <cmath>
#include <iostream>
#include <limits>

#if __has_include("framing_math.h")
#include "framing_math.h"
using namespace apex_framing;

namespace {
bool near(double actual, double expected) {
    return std::abs(actual - expected) <= 1e-9 * std::max(1.0, std::abs(expected));
}

// Independent projection fixtures: forward X, right Y, up Z at zero rotation.
void fixed_cases() {
    Result result{};
    const Vec3 camera{0, 0, 0}, body{300, -50, -60};
    assert(correct(camera, body, {0, 0, 0}, .1, .1, result));
    assert(near(result.location.x, 0));
    assert(near(result.location.y, 5));
    assert(near(result.location.z, 5));
    assert(correct(camera, body, {0, 0, 0}, 0, 0, result));
    assert(near(result.location.y, 0));
    assert(near(result.location.z, 0));
    assert(correct(camera, body, {0, 0, 0}, .2, -.1, result));
    assert(near(result.location.y, 10));
    assert(near(result.location.z, -5));
    assert(correct(camera, {300, 50, -60}, {0, 0, 0}, .1, .1, result));
    assert(near(result.location.y, -5));
    assert(near(result.location.z, 5));
    // A rolled camera's vertical correction follows its up axis, not world Z.
    assert(correct(camera, {300, 60, 50}, {0, 0, 90}, .1, .1, result));
    assert(near(result.location.y, 5));
    assert(near(result.location.z, -5));
}

// Independent Euler basis is used only by this projection oracle.
Vec3 to_world(Vec3 local, Vec3 rotation) {
    const double radians = std::acos(-1.0) / 180;
    const double p = rotation.x * radians, y = rotation.y * radians, r = rotation.z * radians;
    const double cp = std::cos(p), sp = std::sin(p), cy = std::cos(y), sy = std::sin(y);
    const double cr = std::cos(r), sr = std::sin(r);
    return {local.x * cp * cy + local.y * (sr * sp * cy - cr * sy)
                + local.z * (-cr * sp * cy - sr * sy),
            local.x * cp * sy + local.y * (sr * sp * sy + cr * cy)
                + local.z * (-cr * sp * sy + sr * cy),
            local.x * sp - local.y * sr * cp + local.z * cr * cp};
}

double dot(Vec3 a, Vec3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
Vec3 subtract(Vec3 a, Vec3 b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }

void combined_projection() {
    for (Vec3 rotation : {Vec3{0, 0, 0}, {35, -170, 15}, {-70, 80, -45}, {90, 20, 90}}) {
        for (double side : {-50.0, 50.0}) {
            for (double height : {-70.0, -20.0, 25.0}) {
                const Vec3 camera{1000, -800, 400};
                const Vec3 relative = to_world({300, side, height}, rotation);
                const Vec3 body{camera.x + relative.x, camera.y + relative.y, camera.z + relative.z};
                const Vec3 forward = to_world({1, 0, 0}, rotation);
                const Vec3 right = to_world({0, 1, 0}, rotation);
                const Vec3 up = to_world({0, 0, 1}, rotation);
                for (double h : {0.0, .1, .2, .5}) {
                    for (double v : {-.5, -.1, 0.0, .1, .5}) {
                        Result result{};
                        assert(correct(camera, body, rotation, h, v, result));
                        const Vec3 local = subtract(body, result.location);
                        const double depth = dot(local, forward);
                        assert(near(depth, 300));
                        assert(near(dot(local, right) / depth, side * (1 + h) / 300));
                        assert(near(-dot(local, up) / depth,
                                    (-height + v * std::abs(side)) / 300));
                    }
                }
            }
        }
    }
}

void invalid_inputs_and_identity() {
    const double nan = std::numeric_limits<double>::quiet_NaN();
    const double infinity = std::numeric_limits<double>::infinity();
    const Vec3 camera{10, 20, 30}, body{310, -30, -30};
    Result result{};
    assert(correct(camera, body, {35, 12, -17}, 0, 0, result));
    assert(result.location.x == camera.x && result.location.y == camera.y
            && result.location.z == camera.z);
    for (Vec3 bad : {Vec3{nan, 0, 0}, {0, infinity, 0}}) {
        result.location = {111, 222, 333};
        assert(!correct(camera, bad, {0, 0, 0}, .1, .1, result));
        assert(result.location.x == 111 && result.location.y == 222 && result.location.z == 333);
    }
    assert(!correct(camera, body, {nan, 0, 0}, 0, 0, result));
    assert(!correct(camera, body, {0, infinity, 0}, 0, 0, result));
    assert(!correct(camera, {10, 20, 30}, {0, 0, 0}, .1, .1, result));
    assert(!correct(camera, {-10, 20, 30}, {0, 0, 0}, .1, .1, result));
    assert(!correct(camera, {310, 20, 30}, {0, 0, 0}, .1, .1, result));
    assert(!correct(camera, body, {0, 0, 0}, -.1, .1, result));
    for (double invalid : {nan, infinity}) {
        assert(!correct(camera, body, {0, 0, 0}, invalid, .1, result));
        assert(!correct(camera, body, {0, 0, 0}, .1, invalid, result));
    }
}
}

int main() {
    fixed_cases();
    combined_projection();
    invalid_inputs_and_identity();
    std::cout << "RESULTAT: OK (480 distinct projections, atomic refusal)\n";
}
#else
int main() {
    std::cerr << "Framing math missing\n";
    assert(false);
}
#endif

#pragma once

namespace apex_framing {
struct Vec3 { double x, y, z; };
struct Result { Vec3 location; };

// Values are camera-local ratios, not percentages of the viewport.
// The caller supplies a freshly reconstructed historical view and body anchor.
// Zoom changes FOV only and is deliberately not an input to camera placement.
bool correct(Vec3 historical, Vec3 anchor, Vec3 pitch_yaw_roll,
             double horizontal, double vertical, Result& output);

}

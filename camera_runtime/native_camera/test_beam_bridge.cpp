#include <cstddef>
#include "beam_bridge.h"
#include "interaction_alignment.h"
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>

namespace {
bool check(bool condition, const char* name) {
    if (!condition) std::cerr << "FAIL: " << name << '\n';
    return condition;
}

bool near(const double* a, const double* b, double tolerance = 1e-6) {
    for (int i = 0; i < 3; ++i) {
        if (std::abs(a[i] - b[i]) > tolerance) return false;
    }
    return true;
}

// A point given in a view's axes (forward, right, up in cm), as the probe writes them.
void place(const apex_interaction::View& camera, double f, double r, double u, double* out) {
    double ahead[3]{};
    apex_interaction::forward(camera.rotation, ahead);
    const double yaw = camera.rotation[1] * 0.017453292519943295;
    const double pitch = camera.rotation[0] * 0.017453292519943295;
    const double right[] = {-std::sin(yaw), std::cos(yaw), 0};
    const double up[] = {-std::sin(pitch) * std::cos(yaw), -std::sin(pitch) * std::sin(yaw), std::cos(pitch)};
    for (int i = 0; i < 3; ++i) out[i] = camera.origin[i] + f * ahead[i] + r * right[i] + u * up[i];
}
}

int main() {
    bool ok = true;
    // Measured on 2026-10-21 (rayons-1.txt, beam 1): in third person the query starts 181 cm ahead of the camera,
    // 96 cm left and 4 cm below, and runs along the view.
    const apex_interaction::View camera{{-195100.0, 324000.0, 600.0}, {-0.12, 96.09, 0.0}};
    apex_beam::Query game{};
    place(camera, 181, -96, -4, game.origin);
    apex_interaction::forward(camera.rotation, game.direction);
    apex_beam::Query aligned{};
    ok &= check(apex_beam::align_query(game, camera, aligned) == apex_beam::Alignment::written,
                "the hunter's query is moved");
    double wanted[3]{};
    place(camera, 181, 0, 0, wanted);
    ok &= check(near(aligned.origin, wanted), "it starts on the crosshair's line at its own depth");
    ok &= check(near(aligned.direction, game.direction, 1e-12), "and runs along the camera's forward");

    // The dynamic camera turns the view about 2 degrees from the controller: still the crosshair's query.
    apex_beam::Query turned = game;
    const apex_interaction::View controller{{0, 0, 0}, {-0.12, 98.0, 0.0}};
    apex_interaction::forward(controller.rotation, turned.direction);
    ok &= check(apex_beam::align_query(turned, camera, aligned) == apex_beam::Alignment::written,
                "a query 2 degrees off the view is the crosshair's");
    ok &= check(near(aligned.direction, game.direction, 1e-12), "and is sent along the camera's forward");

    const apex_beam::Query kept = aligned;
    apex_beam::Query away = game;
    const apex_interaction::View elsewhere{{0, 0, 0}, {-0.12, 111.0, 0.0}};
    apex_interaction::forward(elsewhere.rotation, away.direction);
    ok &= check(apex_beam::align_query(away, camera, aligned) == apex_beam::Alignment::off_view,
                "a query aimed 15 degrees away is not the crosshair's");
    away.direction[1] = std::numeric_limits<double>::quiet_NaN();
    ok &= check(apex_beam::align_query(away, camera, aligned) == apex_beam::Alignment::off_view,
                "nor one without a direction");
    std::memset(away.direction, 0, sizeof(away.direction));
    ok &= check(apex_beam::align_query(away, camera, aligned) == apex_beam::Alignment::off_view,
                "nor one with a null direction");
    // The beam's first reading on 2026-10-21 started 3.75 m behind the camera (a recycled beam): never moved.
    apex_beam::Query behind = game;
    place(camera, -375, -92, -6, behind.origin);
    ok &= check(apex_beam::align_query(behind, camera, aligned) == apex_beam::Alignment::rejected_view,
                "a query starting behind the camera is left alone");
    apex_beam::Query far = game;
    place(camera, 5000, -96, -4, far.origin);
    ok &= check(apex_beam::align_query(far, camera, aligned) == apex_beam::Alignment::rejected_view,
                "and one starting 50 m away");
    ok &= check(std::memcmp(&aligned, &kept, sizeof(kept)) == 0, "a refusal leaves the result untouched");

    apex_beam::Config config{{apex_interaction::abi, 0, 0x30000, 0x20000, 0x40000, 0}, 0x50000, 0x1A8, 0};
    ok &= check(beam_start(nullptr) == 1, "no configuration");
    config.instigator_offset = 0;
    ok &= check(beam_start(&config) == 1, "an instigator without an offset");
    config.instigator_offset = 0x1A4;
    ok &= check(beam_start(&config) == 1, "a misaligned instigator offset");
    config.instigator_offset = apex_beam::max_field_offset + 8;
    ok &= check(beam_start(&config) == 1, "an instigator beyond the object");
    config.instigator_offset = 0x1A8;
    config.beam_default = 0;
    ok &= check(beam_start(&config) == 1, "no beam class default");
    config.beam_default = 0x50000;
    config.camera.abi += 1;
    ok &= check(beam_start(&config) == 1, "another contract");
    config.camera.abi -= 1;
    // An address nothing occupies in this process: the class default cannot be read.
    config.beam_default = 0x100000000000;
    ok &= check(beam_start(&config) == 2, "an unreadable class default");
    ok &= check(beam_stop() == 0, "stopping what never started");
    apex_beam::Stats stats{};
    ok &= check(beam_stats(&stats) == 0 && !stats.active && !stats.installed && !stats.calls, "empty statistics");
    ok &= check(beam_stats(nullptr) == 1, "statistics need somewhere to go");
    if (!ok) return 1;
    std::cout << "RESULTAT: OK - the hunter's beam starts on the crosshair's line, others are the game's\n";
}

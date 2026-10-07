#include "anchor_contract.h"
#include "ads_compat.h"
#include "camera_builds.h"
#include <cstdio>
#include <cstring>

namespace {
int failures{}, file_error{};
bool eye_valid = true, socket_valid = true, captured = false;
void check(bool value, const char* label) {
    if (!value) { ++failures; std::printf("FAIL: %s\n", label); }
}
}

// Module boundaries are simulated: this executable must never patch the game.
namespace apex_ads {
int verify_module_files_error() { return file_error; }
int compatible_modules_error() {
    // The running ADS runtime has legitimately installed its two HUD detours.
    return file_error ? file_error : static_cast<int>(ERROR_SIGNATURE);
}
bool signature_matches(uintptr_t address, const char* expected) {
    const auto game = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if (address == game + climb_anchor::eye_update_rva
        && std::strcmp(expected, climb_anchor::eye_prefix) == 0) return eye_valid;
    if (address == game + climb_anchor::socket_update_rva
        && std::strcmp(expected, climb_anchor::socket_prefix) == 0) return socket_valid;
    return false;
}
}
namespace climb_anchor {
bool capture(uintptr_t, Session&) {
    captured = true;
    return false;  // Stop safely at the next boundary, before any slot write.
}
bool eligible(const Session&, void*) { return false; }
bool refresh(Session&) { return false; }
bool apply_socket(Update, void*, void*, float, uint64_t) { return false; }
}

int main() {
    check(camera_builds::publish(1), "Steam fixture profile selected");
    check(anchor_start(0) == 2 && captured,
          "owned ADS HUD detours do not reject an intact anchor trial");
    captured = false; file_error = 21;
    check(anchor_start(0) == 21 && !captured,
          "unqualified game file refuses before reading game objects");
    file_error = 20;
    check(anchor_start(0) == 20 && !captured,
          "unqualified SDK refuses before reading game objects");
    file_error = 0; eye_valid = false;
    check(anchor_start(0) == 22 && !captured,
          "modified eye function still refuses the trial");
    eye_valid = true; socket_valid = false;
    check(anchor_start(0) == 22 && !captured,
          "modified socket function still refuses the trial");
    climb_anchor::Statistics stats{};
    check(anchor_stats(&stats) == 0 && !stats.installed && !stats.active,
          "every refusal leaves the camera untouched");
    check(anchor_stop() == 0, "cleanup after refusal is harmless");
    check(anchor_refresh() != 0, "an uninstalled anchor cannot renew ownership");
    std::printf("RESULTAT: %d failure(s)\n", failures);
    return failures ? 1 : 0;
}
